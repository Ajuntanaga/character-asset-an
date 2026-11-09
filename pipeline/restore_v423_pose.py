import bpy,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];assert not bpy.app.is_job_running('RENDER');r=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];p=R/'production_v423_joint_creases/pose_restore.json';saved=json.loads(p.read_text())
for name,value in saved.items():r.pose.bones[name].rotation_euler=value
r.update_tag();bpy.context.view_layer.update()
error=max(abs(r.pose.bones[name].rotation_euler[i]-value[i]) for name,value in saved.items() for i in range(3))
report={'restored_controls':len(saved),'max_rotation_restore_error':error,'drivers':len(r.animation_data.drivers)}
(R/'production_v423_joint_creases/open_pose_check.json').write_text(json.dumps(report,indent=2));p.rename(p.with_name('pose_before_open.json'))
print(json.dumps(report))
