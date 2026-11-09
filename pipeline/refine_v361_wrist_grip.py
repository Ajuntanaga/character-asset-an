"""Apply the opposed thumb and extend the existing hand base inside the sleeve."""
import bpy, json, math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'production_v361_pick_cuffs'
s=bpy.context.scene; r=next(o for o in s.objects if o.name.endswith('_CLOUDRIG_CONTROLS'))
g=bpy.data.objects['V206_GUITAR_ROOT']; gi=g.matrix_world.inverted()
fit=json.loads((OUT/'thumb_fit.json').read_text()); a=list(map(math.radians,fit['angles_degrees']))
for i in range(1,4):
    b=r.pose.bones[f'FK-Finger_Thumb{i}.R']; b.rotation_mode='XYZ'
    b.rotation_euler=(a[0],a[4],a[3]) if i==1 else (a[i-1],0,0)
if not s.get('v361_wrist_extended'):
    for side,sign in (('L',1),('R',-1)):
        hand=next(o for o in s.objects if o.name.endswith('_ANATOMICAL_HAND.'+side))
        hand.data=hand.data.copy(); hand.data.name='V361_Hand_With_Wrist.'+side
        inverse=hand.matrix_world.inverted()
        for v in hand.data.vertices:
            p=hand.matrix_world@v.co
            t=max(0,min(1,(p.z-.902)/.022))
            p.z+=.038*t*t*(3-2*t)
            v.co=inverse@p
        hand.data.update()
        cuff=next(o for o in s.objects if o.name.endswith('_CUFF_PATCH.'+side))
        cuff.data=cuff.data.copy(); cuff.data.name='V361_Closer_Cuff.'+side
        for v in cuff.data.vertices:
            t=max(0,min(1,(v.co.z-.895)/.050)); t=t*t*(3-2*t)
            v.co.x=sign*(.298+.004*t)+(v.co.x-sign*(.298+.004*t))*(.85+.15*t)
            v.co.y=(.008+.0*t)+(v.co.y-.008)*(.72+.28*t)
        cuff.data.update()
    s['v361_wrist_extended']=True
r.update_tag(); bpy.context.view_layer.update()
o=next(o for o in s.objects if o.name.endswith('_ANATOMICAL_HAND.R'))
ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get()); mesh=ev.to_mesh(); transform=gi@ev.matrix_world
coords=[transform@v.co for v in mesh.vertices]
groups=[o.vertex_groups[max(v.groups,key=lambda w:w.weight).group].name for v in mesh.vertices]
faces=[list(p.vertices) for p in mesh.polygons if all('Finger_Index' in groups[i] for i in p.vertices)]
bvh=BVHTree.FromPolygons(coords,faces)
contacts=[]
for p,name in zip(coords,groups):
    if name!='DEF-Finger_Thumb3.R':continue
    near,n,idx,d=bvh.find_nearest(p)
    if d is not None and d<.012:contacts.append({'point':list(p),'index_point':list(near),'normal':list(n),'distance_mm':d*1000,'signed_mm':(p-near).dot(n)*1000})
contacts.sort(key=lambda x:x['distance_mm'])
report={'contacts':contacts,'minimum_signed_mm':min(x['signed_mm'] for x in contacts), 'vertices':[list(p) for p in coords], 'faces':[list(p.vertices) for p in mesh.polygons], 'groups':groups}
ev.to_mesh_clear(); (OUT/'opposition_surface.json').write_text(json.dumps(report))
s.render.engine='BLENDER_WORKBENCH'; s.render.threads_mode='FIXED'; s.render.threads=1
s.render.resolution_x=1000; s.render.resolution_y=1000; s.render.resolution_percentage=100
cam=s.camera; cam.data.type='ORTHO'
for label,pos,target,scale in [('opposed_front',(.68,-.06,.6),(.68,-.06,0),.32),('opposed_side',(.68,.4,.20),(.68,-.04,.04),.30)]:
    cam.location=g.matrix_world@Vector(pos); q=g.matrix_world@Vector(target)
    cam.rotation_euler=(q-cam.location).to_track_quat('-Z','Y').to_euler(); cam.data.ortho_scale=scale
    s.render.filepath=str(OUT/f'v361_{label}.png'); bpy.ops.render.render(write_still=True)
print(json.dumps({'minimum_signed_mm':report['minimum_signed_mm'],'nearest':contacts[:3]}))
