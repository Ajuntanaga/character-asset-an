import bpy,json
from mathutils.bvhtree import BVHTree
s=bpy.context.scene;g=bpy.data.objects["V206_GUITAR_ROOT"];gi=g.matrix_world.inverted();report={}
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


print(json.dumps(report))
