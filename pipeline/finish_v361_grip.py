"""Finish the sleeve fit and add a bone-parented plectrum to the picking grip."""
import bpy, bmesh, json, math
from pathlib import Path
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'production_v361_pick_cuffs'
s = bpy.context.scene
r = next(o for o in s.objects if o.name.endswith('_CLOUDRIG_CONTROLS'))
g = bpy.data.objects['V206_GUITAR_ROOT']
gi = g.matrix_world.inverted()
original = json.loads((OUT / 'before_geometry.json').read_text())
planes = json.loads((ROOT / 'production_v353_cuff_repair/cuff_repair_report.json').read_text())['cuffs']
report = {'cuffs': {}}

for side, sign in (('L', 1), ('R', -1)):
    hand = next(o for o in s.objects if o.name.endswith('_ANATOMICAL_HAND.' + side))
    old = original['objects']['ANATOMICAL_HAND.' + side]
    inv = hand.matrix_world.inverted()
    # Only 12 mm of additional skin is needed inside the overlapping cuff.
    forearm = hand.vertex_groups.get('DEF-Forearm_2.' + side) or hand.vertex_groups.new(name='DEF-Forearm_2.' + side)
    wrist = hand.vertex_groups['DEF-Hand.' + side]
    for v, co in zip(hand.data.vertices, old['rest']):
        p = hand.matrix_world @ Vector(co)
        t = min(1, max(0, (p.z - .900) / .024))
        t = t*t*(3-2*t)
        p.z += .012*t
        v.co = inv @ p
        if t > 0:
            for group in list(v.groups):
                hand.vertex_groups[group.group].remove([v.index])
            wrist.add([v.index], 1-.65*t, 'REPLACE')
            forearm.add([v.index], .65*t, 'REPLACE')
    hand.data.update()

    cuff = next(o for o in s.objects if o.name.endswith('_CUFF_PATCH.' + side))
    source = bpy.data.meshes.get('V353_Cuff_Surface.' + side)
    if source is None:
        raise RuntimeError('Original cuff mesh is not available: ' + side)
    cuff.data = source.copy()
    cuff.data.name = 'V361_Final_Cuff.' + side
    bm = bmesh.new(); bm.from_mesh(cuff.data)
    todo = set(bm.verts); components = []
    while todo:
        queue = [todo.pop()]; component = []
        while queue:
            v = queue.pop(); component.append(v)
            for e in v.link_edges:
                other = e.other_vert(v)
                if other in todo:
                    todo.remove(other); queue.append(other)
        components.append(component)
    components.sort(key=len, reverse=True)
    removed = [v for component in components[1:] for v in component]
    bmesh.ops.delete(bm, geom=removed, context='VERTS')
    intercept, dx, dy = planes[side]['edge_plane']
    for v in bm.verts:
        p = v.co
        edge_z = intercept + .001 + dx*(p.x*sign-.302) + dy*(p.y-.008)
        t = min(1, max(0, (p.z-edge_z)/(.935-edge_z)))
        t = t*t*(3-2*t)
        p.x = sign*(.299+.003*t) + (p.x-sign*.302)*(.50+.50*t)
        p.y = .015-.007*t + (p.y-.008)*(.42+.58*t)
    bm.to_mesh(cuff.data); bm.free(); cuff.data.update()
    report['cuffs'][side] = {'vertices':len(cuff.data.vertices), 'scraps_removed':len(removed)}

fit = json.loads((OUT / 'thumb_clearance.json').read_text())
a = list(map(math.radians, fit['angles_degrees']))
for i in range(1, 4):
    b = r.pose.bones[f'FK-Finger_Thumb{i}.R']; b.rotation_mode='XYZ'
    b.rotation_euler = (a[0],a[4],a[3]) if i==1 else (a[i-1],0,0)
r.update_tag(); bpy.context.view_layer.update()

hand = next(o for o in s.objects if o.name.endswith('_ANATOMICAL_HAND.R'))
ev = hand.evaluated_get(bpy.context.evaluated_depsgraph_get())
mesh = ev.to_mesh(); transform = gi @ ev.matrix_world
coords = [transform @ v.co for v in mesh.vertices]
groups = [hand.vertex_groups[max(v.groups,key=lambda w:w.weight).group].name for v in mesh.vertices]
faces = [list(p.vertices) for p in mesh.polygons if all('Finger_Index' in groups[i] for i in p.vertices)]
bvh = BVHTree.FromPolygons(coords, faces)
contacts = []
for p, name in zip(coords, groups):
    if name != 'DEF-Finger_Thumb3.R': continue
    near,n,idx,d = bvh.find_nearest(p)
    if d is not None and d < .006:
        contacts.append({'point':list(p),'index_point':list(near),'normal':list(n),'distance_mm':d*1000,'signed_mm':(p-near).dot(n)*1000})
contacts.sort(key=lambda c:c['signed_mm'])
report['thumb_contact'] = contacts[:8]
report['minimum_thumb_index_clearance_mm'] = contacts[0]['signed_mm']
ev.to_mesh_clear()

contact = contacts[0]
normal = Vector(contact['normal']).normalized()
index_point = Vector(contact['index_point'])
center = index_point + normal*.0005
direction = Vector((.652,-.003,.0245)) - center
direction = (direction-normal*direction.dot(normal)).normalized()
across = direction.cross(normal).normalized()
# Rounded nylon pick: a broad back, narrow point, and a 0.7 mm edge.
segments = [
    ((0,.022),(.002,.020),(.008,.005),(.008,0)),
    ((.008,0),(.008,-.006),(.004,-.009),(0,-.009)),
    ((0,-.009),(-.004,-.009),(-.008,-.006),(-.008,0)),
    ((-.008,0),(-.008,.005),(-.002,.020),(0,.022)),
]
outline = []
for points in segments:
    for i in range(12):
        t=i/12; u=1-t
        p=[sum(c*w for c,w in zip(axis,(u**3,3*u*u*t,3*u*t*t,t**3))) for axis in zip(*points)]
        outline.append(center+across*p[0]+direction*p[1])
verts=[list(p+normal*z) for z in (-.00035,.00035) for p in outline]
n=len(outline)
polygons=[list(range(n-1,-1,-1)),list(range(n,2*n))]+[[i,(i+1)%n,(i+1)%n+n,i+n] for i in range(n)]
pick = bpy.data.objects.get('V361_NYLON_PICK')
if pick is None:
    data=bpy.data.meshes.new('V361_Plectrum_Mesh'); pick=bpy.data.objects.new('V361_NYLON_PICK',data); s.collection.objects.link(pick)
else:
    pick.data=bpy.data.meshes.new('V361_Plectrum_Mesh')
pick.data.from_pydata(verts,[],polygons); pick.data.update()
mat=bpy.data.materials.get('V361_Nylon_Charcoal') or bpy.data.materials.new('V361_Nylon_Charcoal')
mat.diffuse_color=(.045,.048,.05,1);mat.use_nodes=True
bsdf=mat.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Base Color'].default_value=mat.diffuse_color;bsdf.inputs['Roughness'].default_value=.42
pick.data.materials.append(mat)
bevel=pick.modifiers.get('Rounded edge') or pick.modifiers.new('Rounded edge','BEVEL');bevel.width=.00016;bevel.segments=2
pick.parent=r;pick.parent_type='BONE';pick.parent_bone='IK-Hand.R'
parent_frame=r.matrix_world@r.pose.bones['IK-Hand.R'].matrix@Matrix.Translation((0,r.data.bones['IK-Hand.R'].length,0))
pick.matrix_parent_inverse=parent_frame.inverted();pick.matrix_basis=g.matrix_world
bpy.context.view_layer.update()
error=max(abs(pick.matrix_world[i][j]-g.matrix_world[i][j]) for i in range(4) for j in range(4))
if error>1e-5:raise RuntimeError('Pick parenting displaced geometry: '+str(error))
report['pick']={'parent_bone':pick.parent_bone,'parenting_matrix_error':error,'center_guitar':list(center),'tip_guitar':list(center+direction*.022),'thickness_mm':.7}

# The selector stem was left above the top during the guitar rebuild.
report['selector_objects']=[(o.name,list(gi@o.matrix_world.translation)) for o in s.objects if 'SWITCH' in o.name.upper()]
report['head_meshes']=[(o.name,len(o.data.vertices)) for o in s.objects if o.type=='MESH' and 'BODY_BOUND' in o.name]
(OUT/'final_fit_report.json').write_text(json.dumps(report,indent=2))
s.render.engine='BLENDER_WORKBENCH';s.render.threads_mode='FIXED';s.render.threads=1
s.render.resolution_x=1000;s.render.resolution_y=1000;s.render.resolution_percentage=100
cam=s.camera;cam.data.type='ORTHO'
for label,pos,target,scale in [
    ('final_front',(.68,-.06,.6),(.68,-.06,0),.32),
    ('final_side',(.68,.4,.20),(.68,-.04,.04),.30),
    ('final_fretting',(.285,.025,.6),(.285,.025,0),.32),
]:
    cam.location=g.matrix_world@Vector(pos);q=g.matrix_world@Vector(target)
    cam.rotation_euler=(q-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
    s.render.filepath=str(OUT/f'v361_{label}.png');bpy.ops.render.render(write_still=True)
print(json.dumps(report))
