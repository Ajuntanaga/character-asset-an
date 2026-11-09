"""Render open picking hand, restoring every control and render setting."""
import bpy,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];s=bpy.context.scene;assert not bpy.app.is_job_running('RENDER');r=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];assert len(r.animation_data.drivers)==1957
bones=[b for b in r.pose.bones if b.name.startswith('FK-Finger_') and b.name.endswith('.R')]
saved={b.name:list(b.rotation_euler) for b in bones};old=(s.render.engine,s.render.filepath,s.camera.data.ortho_scale)
try:
 for b in bones:b.rotation_euler=(0,0,0)
 r.update_tag();bpy.context.view_layer.update();s.render.engine='BLENDER_WORKBENCH';s.camera.data.ortho_scale=.35;s.render.filepath=str(R/'production_v413_cuff_fastener/v413_open_hand.png');bpy.ops.render.render(write_still=True)
finally:
 for b in bones:b.rotation_euler=saved[b.name]
 s.render.engine,s.render.filepath,s.camera.data.ortho_scale=old;r.update_tag();bpy.context.view_layer.update()
report={'restored_controls':len(bones),'rig_drivers':len(r.animation_data.drivers),'max_rotation_restore_error':max(abs(b.rotation_euler[i]-saved[b.name][i]) for b in bones for i in range(3))}
(R/'production_v413_cuff_fastener/open_pose_check.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
