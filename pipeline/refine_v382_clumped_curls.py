"""Make each curl a coherent bundle, retaining the reference part and scalp mask."""
from collections import defaultdict
from pathlib import Path
import bisect
import json
import math
import random
import time
import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'production_v382_clumped_curls'
OUT.mkdir(exist_ok=True)
started = time.monotonic()
rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
body = bpy.data.objects['V357_TRIPO_CHARACTER_BODY_BOUND']
assert len(rig.animation_data.drivers) == 1957
assert bpy.data.objects.get('V382_CURL_GROOM') is None
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'production_v381_facial_controls/Character_An_facial_controls_v381.blend'),compress=True)
source = json.loads((ROOT/'production_v371_curl_groom/scalp_surface.json').read_text())
mask = set(json.loads((ROOT/'production_v371_curl_groom/hair_mask.json').read_text())['faces'])
positions = {int(i):Vector(p) for i,p in source['vertices'].items()}
faces = [f for f in source['faces'] if f['id'] in mask]
indices = {old:i for i,old in enumerate(positions)}
bvh = BVHTree.FromPolygons(list(positions.values()),
                          [[indices[v] for v in f['v']] for f in source['faces']],
                          all_triangles=False)
areas,area = [],0.
for face in faces:
    a,b,c = (positions[v] for v in face['v'])
    area += (b-a).cross(c-a).length/2.
    areas.append(area)
rng = random.Random(382)
nprng = np.random.default_rng(382)
spacing = .0074
roots,grid = [],defaultdict(list)
for _ in range(100000):
    face = faces[bisect.bisect_left(areas,rng.random()*area)]
    a,b,c = (positions[v] for v in face['v'])
    u,v = math.sqrt(rng.random()),rng.random()
    weights = (1.-u,u*(1.-v),u*v)
    root = a*weights[0]+b*weights[1]+c*weights[2]
    part = .040+.13*(root.y+.070)
    if root.z>1.720 and -.105<root.y<.065 and abs(root.x-part)<.0035:
        continue
    cell = tuple(math.floor(v/spacing) for v in root)
    neighbors = (p for x in range(cell[0]-1,cell[0]+2)
                 for y in range(cell[1]-1,cell[1]+2)
                 for z in range(cell[2]-1,cell[2]+2)
                 for p in grid.get((x,y,z),()))
    if any((p-root).length_squared<spacing*spacing for p in neighbors):
        continue
    grid[cell].append(root)
    roots.append((root,face,weights))

children,steps = 96,48
t = np.linspace(0.,1.,steps,dtype=np.float32)
points = np.empty((len(roots),children,steps,3),np.float32)
radii = np.empty((len(roots),children,steps),np.float32)
uvs = np.empty((len(roots),children,2),np.float32)
for gi,(root,face,weights) in enumerate(roots):
    normal = Vector(face['normal']).normalized()
    ellipsoid = Vector((root.x/.095**2,(root.y-.012)/.115**2,(root.z-1.682)/.118**2)).normalized()
    if normal.dot(ellipsoid)<0:
        normal.negate()
    normal = (normal*.35+ellipsoid*.65).normalized()
    part = .040+.13*(root.y+.070)
    in_part = root.z>1.720 and -.105<root.y<.065
    direction = Vector((-.85,.30,.05))
    if root.x>part and root.y<.035:
        direction = Vector((.25,.65,-.30))
    elif root.y>.035:
        direction = Vector((0.,.65,-.50))
    tangent = (direction-normal*direction.dot(normal)).normalized()
    across = normal.cross(tangent).normalized()
    theta = rng.uniform(-.25,.25)
    tangent = (tangent*math.cos(theta)+across*math.sin(theta)).normalized()
    across = normal.cross(tangent).normalized()
    topness = min(1.,max(0.,(root.z-1.69)/.08))
    curl_radius = rng.uniform(.0042,.0055)*(.60+.40*topness)
    axial_length = rng.uniform(.011,.015)*(.50+.50*topness)
    turns = rng.uniform(.72,1.05)
    if in_part and abs(root.x-part)<.012:
        curl_radius *= .77
    angle = turns*math.tau*t
    radius = curl_radius*(1.-.12*t)
    height = radius*(1.-np.cos(angle))+.0006+.0005*np.sin(math.pi*t)
    side = radius*np.sin(angle)
    center = (np.asarray(root)[None,:]
              +np.asarray(normal)[None,:]*height[:,None]
              +np.asarray(across)[None,:]*side[:,None]
              +np.asarray(tangent)[None,:]*(axial_length*t)[:,None])
    # Each bundle shares one curl. Fibers only vary within its cross section.
    # Their stable offsets retain clump thickness through the free tip.
    radial = (np.asarray(normal)[None,:]*np.cos(angle)[:,None]
              +np.asarray(across)[None,:]*np.sin(angle)[:,None])
    spread_angle = nprng.uniform(0.,math.tau,children)
    spread_radius = np.sqrt(nprng.uniform(0.,1.,children))*rng.uniform(.00060,.00085)
    offset_radial = (np.cos(spread_angle)*spread_radius)[:,None,None]*radial[None,:,:]
    offset_axial = ((np.sin(spread_angle)*spread_radius)[:,None,None]
                    *np.asarray(tangent)[None,None,:])
    spread = (.82+.18*np.exp(-4.*t))[None,:,None]
    block = center[None,:,:]+(offset_radial+offset_axial)*spread
    wave_phase = nprng.uniform(0.,math.tau,children)
    wave_amplitude = nprng.uniform(.000008,.000065,children)
    wave = wave_amplitude[:,None]*np.sin(wave_phase[:,None]+t[None,:]*math.tau*2.)
    block += radial[None,:,:]*wave[:,:,None]
    for j,p in enumerate(center):
        near,n,_,_ = bvh.find_nearest(Vector(p))
        if near is not None:
            clearance = (Vector(p)-near).dot(n)
            if clearance<.0010:
                block[:,j,:] += np.asarray(n)*(.0010-clearance)
    for k in range(children):
        near,n,_,_ = bvh.find_nearest(Vector(block[k,0]))
        if near is not None:
            block[k,0] = near+n*.00006
    if in_part:
        edge = .040+.13*(block[:,:,1]+.070)
        if root.x<part:
            block[:,:,0] = np.minimum(block[:,:,0],edge-.0015)
        else:
            block[:,:,0] = np.maximum(block[:,:,0],edge+.0015)
    points[gi] = block
    radius0 = nprng.uniform(.000029,.000043,children)
    radii[gi] = radius0[:,None]*(1.-.58*t**2)[None,:]
    radii[gi,:,-1] = .000004
    uvs[gi] = np.asarray(weights)@np.asarray(face['uv'])

visibility = {}
for name in ('V370_CURL_GROOM','V371_CURL_GROOM','V373_CURL_GROOM','V375_CURL_GROOM','V376_CURL_GROOM'):
    old = bpy.data.objects.get(name)
    if old:
        visibility[name] = {'render':old.hide_render,'viewport':old.hide_get()}
        old.hide_render = True
        old.hide_set(True)
(OUT/'previous_visibility.json').write_text(json.dumps(visibility,indent=2))
curves = bpy.data.hair_curves.new('V382_CLUMPED_CURL_STRANDS')
curves.add_curves([steps]*(len(roots)*children))
curves.set_types(type='CATMULL_ROM')
curves.position_data.foreach_set('vector',points.ravel())
curves.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',radii.ravel())
curves.attributes.new('surface_uv_coordinate','FLOAT2','CURVE').data.foreach_set('vector',uvs.ravel())
curves.surface = body
curves.surface_uv_map = body.data.uv_layers.active.name
curves.surface_collision_distance = .0002
mat = bpy.data.materials['V376_BLACK_CURL_FIBER'].copy()
mat.name = 'V382_BLACK_CURL_FIBER'
shader = next(n for n in mat.node_tree.nodes if n.type=='BSDF_HAIR_PRINCIPLED')
shader.inputs['Roughness'].default_value = .29
shader.inputs['Random Roughness'].default_value = .12
curves.materials.append(mat)
obj = bpy.data.objects.new('V382_CURL_GROOM',curves)
bpy.context.scene.collection.objects.link(obj)
bone = rig.pose.bones['DEF-Head']
frame = rig.matrix_world@bone.matrix@Matrix.Translation((0,bone.bone.length,0))
obj.parent,obj.parent_type,obj.parent_bone = rig,'BONE','DEF-Head'
obj.matrix_parent_inverse = frame.inverted()
obj.matrix_basis = Matrix.Identity(4)
obj['guide_count'],obj['strand_count'] = len(roots),len(roots)*children
obj['reference'] = 'character_an_front_v1.png'
curves.update_tag()
bpy.context.view_layer.update()
report = {'guides':len(roots),'strands':len(roots)*children,'points':len(curves.points),
          'root_spacing_m':spacing,'build_seconds':time.monotonic()-started,
          'rig_drivers':len(rig.animation_data.drivers)}
(OUT/'groom_report.json').write_text(json.dumps(report,indent=2))
scene = bpy.context.scene
scene.cycles.samples = 48
scene.cycles.use_denoising = True
scene.render.resolution_x = scene.render.resolution_y = 800
scene.render.threads_mode,scene.render.threads = 'FIXED',4
scene.camera.data.ortho_scale = .37
scene.camera.location = (0,-1.4,1.66)
scene.camera.rotation_euler = (Vector((0,0,1.65))-scene.camera.location).to_track_quat('-Z','Y').to_euler()
scene.render.filepath = str(OUT/'v382_clumped_curls_front.png')
bpy.ops.render.render(write_still=True)
print(json.dumps(report))
