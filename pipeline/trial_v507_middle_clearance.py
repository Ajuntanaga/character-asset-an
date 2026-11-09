import bpy,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1];out=root/'production_v507_curl_clearance'
assert not bpy.app.is_job_running('RENDER') and 'v506' in bpy.data.filepath
rig=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];h=bpy.data.objects['V357_ANATOMICAL_HAND.R'];bs=[rig.pose.bones[f'FK-Finger_Middle{i}.R'] for i in (1,2,3)]
p=out/'original_pose.json';assert not p.exists();p.write_text(json.dumps({b.name:[list(row) for row in b.matrix_basis] for b in bs}))
c=json.loads((out/'contacts.json').read_text())['contacts'][0];vi=c['vertex'];away=np.array(c['away']);x0=np.array([b.rotation_euler.x for b in bs]);x=x0.copy()
def position(x):
 for b,v in zip(bs,x):b.rotation_euler.x=float(v)
 rig.update_tag();bpy.context.view_layer.update();e=h.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();v=np.array(e.matrix_world@m.vertices[vi].co);e.to_mesh_clear();return v
start=position(x);target=start+away*.002
for _ in range(5):
 v=position(x);j=np.column_stack([(position(x+np.eye(3)[i]*.001)-v)/.001 for i in range(3)])
 step=np.linalg.solve(j.T@j+np.eye(3)*.00001,j.T@(target-v));x=np.clip(x+step,x0-math.radians(8),x0+math.radians(8))
end=position(x);report={'angles_degrees':np.degrees(x).tolist(),'delta_degrees':np.degrees(x-x0).tolist(),'vertex_motion_mm':((end-start)*1000).tolist(),'target_error_mm':float(np.linalg.norm(end-target)*1000)}
(out/'fit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
f=root/'pipeline/check_v458_grip_fit.py';s=f.read_text().replace('production_v458_grip_fit/check.json','production_v507_curl_clearance/check.json');exec(compile(s,str(f),'exec'),{'__file__':str(f)})
