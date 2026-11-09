"""Bounded inner-joint crease trial; discover flex direction from live rig."""
import bpy,json,math
from mathutils import Vector
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'production_v515_joint_fold';out.mkdir(exist_ok=True)
assert 'v514' in bpy.data.filepath and not bpy.app.is_job_running('RENDER')
h=bpy.data.objects['V357_ANATOMICAL_HAND.R'];r=bpy.data.objects['V357_CLOUDRIG_CONTROLS']
coords=[v.co.copy() for v in h.data.vertices]
names=[f'FK-Finger_{f}{i}.R' for f in ('Middle','Ring','Pinky') for i in (1,2,3)]
pose={n:r.pose.bones[n].matrix_basis.copy() for n in names}
p=out/'original.json';assert not p.exists();p.write_text(json.dumps({'coordinates':[list(v) for v in coords],'pose':{n:[list(row) for row in m] for n,m in pose.items()}}))
bones=json.loads((root/'production_v359_hand_weights/rest_hand_data.json').read_text())['bones']
weights=[{h.vertex_groups[g.group].name:g.weight for g in v.groups} for v in h.data.vertices]
adj=[set() for v in h.data.vertices]
for face in h.data.polygons:
 for i in face.vertices:adj[i].update(face.vertices)
f=root/'pipeline/review_v492_isolated_palm.py'
def update():r.update_tag();h.data.update();h.update_tag();bpy.context.view_layer.update()
def render(label):
 update();s=f.read_text().replace('production_v492_palm_review','production_v515_joint_fold/'+label).replace('out.mkdir(exist_ok=True)','out.mkdir(parents=True,exist_ok=True)')
 exec(compile(s,str(f),'exec'),{'__file__':str(f)})
report=[]
try:
 render('baseline')
 for finger in ('Middle','Ring','Pinky'):
  for joint in (2,3):
   ctrl=r.pose.bones[f'FK-Finger_{finger}{joint}.R'];base=ctrl.rotation_euler.x
   parent=r.pose.bones[f'DEF-Finger_{finger}{joint-1}.R'];child=r.pose.bones[f'DEF-Finger_{finger}{joint}.R']
   ctrl.rotation_euler.x=0;update();a=parent.matrix.inverted()@child.tail
   ctrl.rotation_euler.x=.05;update();b=parent.matrix.inverted()@child.tail
   direction=(h.matrix_world.inverted().to_3x3()@r.matrix_world.to_3x3()@parent.bone.matrix_local.to_3x3()@(b-a)).normalized()
   ctrl.rotation_euler.x=base;update()
   n1=f'DEF-Finger_{finger}{joint-1}.R';n2=f'DEF-Finger_{finger}{joint}.R'
   ring={i for i,w in enumerate(weights) if w.get(n1,0)>.05 and w.get(n2,0)>.05}
   near=set().union(*(adj[i] for i in ring))-ring
   origin=Vector(bones[n2.replace('.R','.L')]['head']);axis=(Vector(bones[n2.replace('.R','.L')]['tail'])-origin).normalized()
   direction=(direction-axis*direction.dot(axis)).normalized()
   t=max(0,min(1,(base-math.radians(20))/math.radians(45)));q=t*t*(3-2*t)
   changed=0
   for i in ring|near:
    delta=coords[i]-origin;radial=delta-axis*delta.dot(axis);inner=radial.dot(direction)
    if inner<=0:continue
    amount=q*(1 if i in ring else .35)*min(.0012,.25*inner)
    h.data.vertices[i].co-=direction*amount;changed+=amount>1e-8
   report.append({'finger':finger,'joint':joint,'inner_direction':list(direction),'ring':len(ring),'changed':changed,'q':q})
 render('trial')
 (out/'candidate_coordinates.json').write_text(json.dumps([list(v.co) for v in h.data.vertices]))
 (out/'changes.json').write_text(json.dumps(report,indent=2))
finally:
 for v,co in zip(h.data.vertices,coords):v.co=co
 for n,m in pose.items():r.pose.bones[n].matrix_basis=m
 update();assert len(r.animation_data.drivers)==1957
 (out/'restored.json').write_text(json.dumps({'restored':True,'drivers':1957}))
print(json.dumps(report))
