import bpy,json,math
import numpy as np
from pathlib import Path
root=Path('/home/ajuntanaga/Projects/Blender/Character Asset_An');out=root/'production_v501_pick_refit';out.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
r=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];assert len(r.animation_data.drivers)==1957
assert 'v500' in bpy.data.filepath
bs=[r.pose.bones[f'FK-Finger_Index{i}.R'] for i in (1,2,3)]
print('BONES',[(b.name,b.rotation_mode) for b in bs])
backup={b.name:[list(row) for row in b.matrix_basis] for b in bs};(out/'original_pose.json').write_text(json.dumps(backup,indent=2))
def points():
 bpy.context.view_layer.update();b=r.pose.bones['DEF-Finger_Index3.R'];return np.array([*b.head,*b.tail])
bs[0].scale.y=1;target=points();bs[0].scale.y=1.25;points()
x0=np.array([*bs[0].rotation_euler,bs[1].rotation_euler.x,bs[2].rotation_euler.x]);x=x0.copy()
def setx(v):
 bs[0].rotation_euler=v[:3];bs[1].rotation_euler.x=v[3];bs[2].rotation_euler.x=v[4]
def residual(v):
 setx(v);return np.r_[(points()-target)*1000,(v-x0)*.2]
for it in range(70):
 f=residual(x);J=np.column_stack([(residual(x+np.eye(5)[k]*.001)-f)/.001 for k in range(5)])
 step=np.linalg.solve(J.T@J+np.eye(5)*.5,-J.T@f);step*=min(1,.10/max(abs(step)))
 improved=False
 for a in (1,.5,.25,.125,.0625):
  y=np.clip(x+a*step,x0-1.2,x0+1.2)
  if np.linalg.norm(residual(y))<np.linalg.norm(f):x=y;improved=True;break
 if not improved:break
setx(x);actual=points();report={'target':target.tolist(),'actual':actual.tolist(),'error_mm':float(np.linalg.norm(actual-target)*1000),'delta_degrees':np.degrees(x-x0).tolist(),'drivers':len(r.animation_data.drivers)}
(out/'fit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
f=root/'pipeline/check_v458_grip_fit.py';exec(f.read_text().replace("production_v458_grip_fit/check.json","production_v501_pick_refit/check.json"),{})
