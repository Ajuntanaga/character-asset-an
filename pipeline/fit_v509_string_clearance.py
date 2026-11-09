import bpy,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1];out=root/'production_v509_loose_pick_pose'
assert not bpy.app.is_job_running('RENDER')
r=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];h=bpy.data.objects['V357_ANATOMICAL_HAND.R'];g=bpy.data.objects['V206_GUITAR_ROOT']
normal=np.array((g.matrix_world.to_3x3()@Vector((0,0,1))).normalized())
contacts=json.loads((out/'contacts.json').read_text())['contacts'];report={}
for digit,si in [('Ring',3),('Middle',5)]:
 c=contacts[si-1];vi=c['vertex'];bs=[r.pose.bones[f'FK-Finger_{digit}{i}.R'] for i in (1,2,3)];x0=np.array([b.rotation_euler.x for b in bs]);x=x0.copy()
 def position(x):
  for b,v in zip(bs,x):b.rotation_euler.x=float(v)
  r.update_tag();bpy.context.view_layer.update();e=h.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh()
  v=np.array(e.matrix_world@m.vertices[vi].co);e.to_mesh_clear();return v
 start=position(x);target=start+normal*.004
 for _ in range(6):
  v=position(x);j=np.column_stack([(position(x+np.eye(3)[i]*.001)-v)/.001 for i in range(3)])
  step=np.linalg.solve(j.T@j+np.eye(3)*.00001,j.T@(target-v));x=np.clip(x+step,x0-math.radians(12),x0+math.radians(12))
 end=position(x);report[digit]={'angles':np.degrees(x).tolist(),'motion_mm':((end-start)*1000).tolist(),'error_mm':float(np.linalg.norm(end-target)*1000)}
(out/'fit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
f=root/'pipeline/check_v458_grip_fit.py';exec(compile(f.read_text().replace('production_v458_grip_fit/check.json','production_v509_loose_pick_pose/fitted_check.json'),str(f),'exec'),{'__file__':str(f)})
p=root/'pipeline/render_preview_request.json';request=json.loads(p.read_text());request['output']='production_v509_loose_pick_pose/fitted.png';p.write_text(json.dumps(request))
f=root/'pipeline/render_preview_job.py';exec(compile(f.read_text(),str(f),'exec'),{'__file__':str(f)})
