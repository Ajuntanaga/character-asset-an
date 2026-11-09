import bpy,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
root=Path('/home/ajuntanaga/Projects/Blender/Character Asset_An');out=root/'production_v458_grip_fit';out.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
r=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];g=bpy.data.objects['V206_GUITAR_ROOT'];gi=g.matrix_world.inverted();p=bpy.data.objects['V361_NYLON_PICK']
center=Vector((.636374,-.021557,.051348));rot=Matrix.Rotation(math.radians(35),4,'Y')
local_transform=Matrix.Translation(center)@rot@Matrix.Translation(-center)
tip=min((gi@p.matrix_world@v.co for v in p.data.vertices),key=lambda v:v.z)
turned=local_transform@tip
local_transform=Matrix.Translation((0,0,.029-turned.z))@local_transform
report={'transform':[list(row) for row in local_transform],'original_tip':list(tip),'new_tip':list(local_transform@tip),'fingers':{}}
for finger in ('Index','Thumb'):
 bs=[r.pose.bones[f'FK-Finger_{finger}{i}.R'] for i in (1,2,3)]
 params=[(bs[0],0),(bs[0],1),(bs[0],2),(bs[1],0),(bs[2],0)]
 initial=np.array([b.rotation_euler[i] for b,i in params]);a=initial.copy()
 def points():
  b=r.pose.bones[f'DEF-Finger_{finger}3.R']
  return np.array([list(gi@r.matrix_world@v) for v in (b.head,b.tail)]).reshape(-1)
 original_points=points();target=np.array([list(local_transform@Vector(v)) for v in original_points.reshape(2,3)]).reshape(-1)
 def evaluate(x):
  for (b,i),value in zip(params,x):b.rotation_euler[i]=float(value)
  r.update_tag();bpy.context.view_layer.update()
  return np.r_[(points()-target)*1000,(x-initial)*.5]
 for iteration in range(60):
  f=evaluate(a);cols=[]
  for j in range(5):
   shifted=a.copy();shifted[j]+=.002;cols.append((evaluate(shifted)-f)/.002)
  jac=np.array(cols).T;step=np.linalg.lstsq(np.vstack([jac,np.eye(5)*.8]),np.r_[-f,np.zeros(5)],rcond=None)[0]
  step*=min(1.,.10/max(np.max(np.abs(step)),1e-9))
  accepted=False
  for scale in (1.,.5,.25,.125,.0625,.03125):
   candidate=np.clip(a+step*scale,initial-math.radians(65),initial+math.radians(65))
   if np.linalg.norm(evaluate(candidate))<np.linalg.norm(f):
    a=candidate;accepted=True;break
  if not accepted:break
  if np.linalg.norm(step)<.00001:break
 evaluate(a)
 report['fingers'][finger]={'before':initial.tolist(),'after':a.tolist(),'target':target.tolist(),'actual':points().tolist(),'error_mm':float(np.linalg.norm(points()-target)*1000)}
# Move pick with the intended shared grip transform; skin contact checked separately.
p.matrix_world=g.matrix_world@local_transform@gi@p.matrix_world
bpy.context.view_layer.update()
(out/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
(root/'pipeline/render_preview_request.json').write_text(json.dumps({'output':'production_v458_grip_fit/v458_wrists.png','resolution':[1000,700],'samples':24,'scale':.9,'camera':[.25,-3.5,1.42],'target':[0,-.15,1.1]}))
f=root/'pipeline/render_preview_job.py';exec(compile(f.read_text(),str(f),'exec'),dict(globals(),__file__=str(f)))
