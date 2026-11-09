import bpy,json,math,numpy as np
from pathlib import Path
from mathutils import Vector
root=Path('/home/ajuntanaga/Projects/Blender/Character Asset_An');out=root/'production_v458_grip_fit'
assert not bpy.app.is_job_running('RENDER')
r=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];g=bpy.data.objects['V206_GUITAR_ROOT'];gi=g.matrix_world.inverted()
bs=[r.pose.bones[f'FK-Finger_Thumb{i}.R'] for i in (1,2,3)];params=[(bs[0],0),(bs[0],1),(bs[0],2),(bs[1],0),(bs[2],0)]
a=np.array([b.rotation_euler[i] for b,i in params]);initial=a.copy()
bone=r.pose.bones['DEF-Finger_Thumb3.R'];point=Vector((.6373836398,-.0206856206,.0477777757));local=(gi@r.matrix_world@bone.matrix).inverted()@point
target=np.array(point-Vector((.969659,.148608,.194106))*.0022)
def f(x):
 for (b,i),v in zip(params,x):b.rotation_euler[i]=float(v)
 r.update_tag();bpy.context.view_layer.update()
 p=gi@r.matrix_world@bone.matrix@local
 return np.r_[(np.array(p)-target)*1000,(x-initial)*2]
for it in range(20):
 v=f(a);jac=[]
 for j in range(5):
  x=a.copy();x[j]+=.001;jac.append((f(x)-v)/.001)
 step=np.linalg.lstsq(np.array(jac).T,-v,rcond=None)[0];step*=min(1,.06/max(abs(step)))
 for scale in (1,.5,.25,.125):
  if np.linalg.norm(f(a+step*scale))<np.linalg.norm(v):a+=step*scale;break
 else:break
f(a)
# Raise the complete relaxed hand slightly to clear string thickness.
b=r.pose.bones['IK-Hand.R'];mat=b.matrix.copy();mat.translation+=r.matrix_world.inverted().to_3x3()@g.matrix_world.to_3x3()@Vector((0,0,.0015));b.matrix=mat;r.update_tag();bpy.context.view_layer.update()
(out/'thumb_finish.json').write_text(json.dumps({'before':initial.tolist(),'after':a.tolist(),'wrist_lift_mm':1.5},indent=2))
exec(compile((root/'pipeline/inspect_v458_pinch.py').read_text(),'pinch','exec'))
exec(compile((root/'pipeline/check_v458_grip_fit.py').read_text(),'clearance','exec'))
(root/'pipeline/render_preview_request.json').write_text(json.dumps({'output':'production_v458_grip_fit/v458_wrists_final.png','resolution':[1000,700],'samples':24,'scale':.9,'camera':[.25,-3.5,1.42],'target':[0,-.15,1.1]}))
f=root/'pipeline/render_preview_job.py';exec(compile(f.read_text(),str(f),'exec'),dict(globals(),__file__=str(f)))
