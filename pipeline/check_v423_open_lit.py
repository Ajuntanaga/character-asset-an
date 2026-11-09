"""Start a temporary open-hand lit preview; pair with restore_v423_pose.py."""
import bpy,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];s=bpy.context.scene;r=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];assert not bpy.app.is_job_running('RENDER')
p=R/'production_v423_joint_creases/pose_restore.json'
assert not p.exists(),'Restore the prior pose test first'
bones=[b for b in r.pose.bones if b.name.startswith('FK-Finger_') and b.name.endswith('.R')]
p.write_text(json.dumps({b.name:list(b.rotation_euler) for b in bones},indent=2))
for b in bones:b.rotation_euler=(0,0,0)
r.update_tag();bpy.context.view_layer.update()
s.render.filepath=str(R/'production_v423_joint_creases/v423_open_lit.png');s.camera.data.ortho_scale=.35
bpy.ops.render.render('INVOKE_DEFAULT',write_still=True)
print('Open-hand render started; do not save until restore_v423_pose.py runs')
