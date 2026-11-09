"""Build compact tangent-growing curls in the existing Blender MCP scene."""
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
OUT = ROOT/'production_v376_face_refinement'
OUT.mkdir(exist_ok=True)
started = time.monotonic()
rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
body = bpy.data.objects['V357_TRIPO_CHARACTER_BODY_BOUND']
assert len(rig.animation_data.drivers) == 1957
assert bpy.data.objects.get('V376_CURL_GROOM') is None
source = json.loads((ROOT/'production_v371_curl_groom/scalp_surface.json').read_text())
mask = set(json.loads((ROOT/'production_v371_curl_groom/hair_mask.json').read_text())['faces'])
positions = {int(i): Vector(p) for i,p in source['vertices'].items()}
faces = [f for f in source['faces'] if f['id'] in mask]
indices = {old:i for i,old in enumerate(positions)}
bvh = BVHTree.FromPolygons(list(positions.values()), [[indices[v] for v in f['v']] for f in source['faces']], all_triangles=False)
areas, area = [], 0.
for f in faces:
    a,b,c = (positions[v] for v in f['v'])
    area += (b-a).cross(c-a).length/2
    areas.append(area)
rng = random.Random(376)
nprng = np.random.default_rng(376)
spacing = .0038
roots, grid = [], defaultdict(list)
for _ in range(130000):
    face = faces[bisect.bisect_left(areas,rng.random()*area)]
    a,b,c = (positions[v] for v in face['v'])
    u,v = math.sqrt(rng.random()), rng.random()
    w = (1-u,u*(1-v),u*v)
    root = a*w[0]+b*w[1]+c*w[2]
    part = .040+.13*(root.y+.070)
    in_part = root.z>1.720 and -.105<root.y<.065
    if in_part and abs(root.x-part)<.0023:
        continue
    cell = tuple(math.floor(v/spacing) for v in root)
    neighbors = (p for x in range(cell[0]-1,cell[0]+2)
                 for y in range(cell[1]-1,cell[1]+2)
                 for z in range(cell[2]-1,cell[2]+2)
                 for p in grid.get((x,y,z),()))
    if any((p-root).length_squared < spacing*spacing for p in neighbors):
        continue
    grid[cell].append(root)
    roots.append((root,face,w))

children, steps = 22, 48
t = np.linspace(0.,1.,steps,dtype=np.float32)
points = np.empty((len(roots),children,steps,3),np.float32)
radii = np.empty((len(roots),children,steps),np.float32)
uvs = np.empty((len(roots),children,2),np.float32)
for gi,(root,face,w) in enumerate(roots):
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
    theta = rng.uniform(-.65,.65)
    tangent = (tangent*math.cos(theta)+across*math.sin(theta)).normalized()
    across = normal.cross(tangent).normalized()
    topness = min(1.,max(0.,(root.z-1.69)/.08))
    curl_radius = rng.uniform(.0025,.0040)*(.70+.30*topness)
    axial_length = rng.uniform(.0055,.010)*(.65+.35*topness)
    turns = rng.uniform(.85,1.55)
    if in_part and abs(root.x-part)<.010:
        curl_radius *= .70
    # A curl starts at the bottom of its ring and travels along the scalp.
    # Child fibers retain width at their tips instead of collapsing to a spike.
    child_radius = curl_radius*nprng.uniform(.87,1.13,children)
    child_turns = turns*nprng.uniform(.85,1.15,children)
    child_length = axial_length*nprng.uniform(.82,1.15,children)
    phase = nprng.uniform(-.24,.24,children)
    angle = phase[:,None]+child_turns[:,None]*math.tau*t[None,:]
    radius = child_radius[:,None]*(1.-.20*t[None,:])
    height = radius*(1.-np.cos(angle))
    side = radius*(np.sin(angle)-np.sin(phase)[:,None])
    along = child_length[:,None]*t[None,:]
    lift = .00035+.0014*np.sin(math.pi*t[None,:])
    block = (np.asarray(root)[None,None,:]
             +np.asarray(normal)[None,None,:]*(height+lift)[:,:,None]
             +np.asarray(across)[None,None,:]*side[:,:,None]
             +np.asarray(tangent)[None,None,:]*along[:,:,None])
    spread_angle = nprng.uniform(0.,math.tau,children)
    spread_radius = np.sqrt(nprng.uniform(0.,1.,children))*rng.uniform(.0006,.0010)
    offsets = (np.cos(spread_angle)[:,None]*np.asarray(tangent)+np.sin(spread_angle)[:,None]*np.asarray(across))*spread_radius[:,None]
    block += offsets[:,None,:]*(.55+.45*np.exp(-3*t))[None,:,None]
    # Project the shared guide, then apply its clearance correction to fibers.
    mean = block.mean(axis=0)
    for j,p in enumerate(mean):
        near,n,_,_ = bvh.find_nearest(Vector(p))
        if near is not None:
            clearance = (Vector(p)-near).dot(n)
            if clearance<.0006:
                block[:,j,:] += np.asarray(n)*(.0006-clearance)
    for k in range(children):
        near,n,_,_ = bvh.find_nearest(Vector(block[k,0]))
        if near is not None:
            block[k,0] = near+n*.00006
    if in_part:
        edge = .040+.13*(block[:,:,1]+.070)
        if root.x<part:
            block[:,:,0] = np.minimum(block[:,:,0],edge-.0010)
        else:
            block[:,:,0] = np.maximum(block[:,:,0],edge+.0010)
    points[gi] = block
    radius0 = nprng.uniform(.000029,.000043,children)
    radii[gi] = radius0[:,None]*(1.-.60*t**2)[None,:]
    radii[gi,:,-1] = .000004
    uvs[gi] = np.asarray(w)@np.asarray(face['uv'])

for name in ('V370_CURL_GROOM','V371_CURL_GROOM','V373_CURL_GROOM','V375_CURL_GROOM'):
    old = bpy.data.objects.get(name)
    if old:
        old.hide_render = True
        old.hide_set(True)
curves = bpy.data.hair_curves.new('V376_COMPACT_CURL_STRANDS')
curves.add_curves([steps]*(len(roots)*children))
curves.set_types(type='CATMULL_ROM')
curves.position_data.foreach_set('vector',points.ravel())
curves.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',radii.ravel())
curves.attributes.new('surface_uv_coordinate','FLOAT2','CURVE').data.foreach_set('vector',uvs.ravel())
curves.surface = body
curves.surface_uv_map = body.data.uv_layers.active.name
curves.surface_collision_distance = .0002
mat = bpy.data.materials['V375_BLACK_CURL_FIBER'].copy()
mat.name = 'V376_BLACK_CURL_FIBER'
shader = next(n for n in mat.node_tree.nodes if n.type=='BSDF_HAIR_PRINCIPLED')
shader.inputs['Roughness'].default_value = .34
shader.inputs['Random Roughness'].default_value = .18
curves.materials.append(mat)
obj = bpy.data.objects.new('V376_CURL_GROOM',curves)
bpy.context.scene.collection.objects.link(obj)
bone = rig.pose.bones['DEF-Head']
frame = rig.matrix_world@bone.matrix@Matrix.Translation((0,bone.bone.length,0))
obj.parent, obj.parent_type, obj.parent_bone = rig,'BONE','DEF-Head'
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
scene.render.filepath = str(OUT/'v376_compact_curls_front.png')
bpy.ops.render.render(write_still=True)
print(json.dumps(report))
