"""Anatomical section trial: planar dorsal shoulders and tapered shafts."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1];out=root/'production_v518_finger_sections';out.mkdir(exist_ok=True)
h=bpy.data.objects['V357_ANATOMICAL_HAND.R'];rig=bpy.data.objects['V357_CLOUDRIG_CONTROLS']
assert 'v514' in bpy.data.filepath and not bpy.app.is_job_running('RENDER')
coords=[v.co.copy() for v in h.data.vertices]
names=[f'FK-Finger_{f}{j}.R' for f in ('Index','Middle','Ring','Pinky') for j in (1,2,3)]
pose={n:rig.pose.bones[n].matrix_basis.copy() for n in names}
assert not (out/'original.json').exists()
(out/'original.json').write_text(json.dumps({'coordinates':[list(v) for v in coords],'pose':{n:[list(row) for row in m] for n,m in pose.items()}}))
bones=json.loads((root/'production_v359_hand_weights/rest_hand_data.json').read_text())['bones']
nails={i for p in h.data.polygons if p.material_index==1 for i in p.vertices}
changes=[]
try:
 for v in h.data.vertices:
  if v.index in nails:continue
  weights={h.vertex_groups[g.group].name:g.weight for g in v.groups}
  choices=[]
  for finger in ('Index','Middle','Ring','Pinky'):
   weight=sum(weights.get(f'DEF-Finger_{finger}{j}.R',0) for j in (1,2,3))
   if weight<.8:continue
   for j in (1,2,3):
    b=bones[f'DEF-Finger_{finger}{j}.L'];a=Vector(b['head']);z=Vector(b['tail']);axis=(z-a).normalized();length=(z-a).length
    t=(v.co-a).dot(axis)/length
    if -.05<=t<=1.05:
     center=a+axis*(t*length);rad=v.co-center
     choices.append((rad.length,finger,j,t,axis,rad,weight))
  if not choices:continue
  _,finger,j,t,axis,rad,weight=min(choices,key=lambda c:c[0])
  depth=(Vector((0,1,0))-axis*axis.y).normalized();width=depth.cross(axis).normalized()
  x=rad.dot(width);y=rad.dot(depth);radius=math.hypot(x,y)
  if radius<1e-6:continue
  # Soft-square the dorsal half, retaining the convex palmar pad.
  cx=abs(x)/radius;cy=abs(y)/radius
  blend=min(1,max(0,t/.25)) if j==1 else (min(1,max(0,(1-t)/.35)) if j==3 else 1)
  dorsal=max(0,min(1,-y/(radius*.35)))
  xx=math.copysign(radius*cx**.72,x) if cx else 0
  yy=math.copysign(radius*cy**.72,y) if cy else 0
  dx=(xx-x)*dorsal-.10*x
  dy=(yy-y)*dorsal-(.12*y if y<0 else 0)
  delta=(width*dx+depth*dy)*blend*weight
  if delta.length>.002:delta*=.002/delta.length
  v.co+=delta
  changes.append({'vertex':v.index,'delta':list(delta)})
 def render(label):
  h.data.update();h.update_tag();rig.update_tag();bpy.context.view_layer.update()
  f=root/'pipeline/review_v492_isolated_palm.py'
  code=f.read_text().replace('production_v492_palm_review','production_v518_finger_sections/'+label).replace('out.mkdir(exist_ok=True)','out.mkdir(parents=True,exist_ok=True)')
  exec(compile(code,str(f),'exec'),{'__file__':str(f)})
 render('playing')
 for n in names:rig.pose.bones[n].rotation_euler.x=0
 render('open')
 (out/'candidate_coordinates.json').write_text(json.dumps([list(v.co) for v in h.data.vertices]))
 (out/'changes.json').write_text(json.dumps(changes))
finally:
 for v,co in zip(h.data.vertices,coords):v.co=co
 for n,m in pose.items():rig.pose.bones[n].matrix_basis=m
 h.data.update();h.update_tag();rig.update_tag();bpy.context.view_layer.update()
 assert len(rig.animation_data.drivers)==1957
 (out/'restored.json').write_text(json.dumps({'restored':True,'drivers':1957}))
print('V518 restored after comparison',len(changes))
