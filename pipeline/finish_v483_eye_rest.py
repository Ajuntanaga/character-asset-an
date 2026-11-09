import bpy,json
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'production_v483_eye_rest'
assert not bpy.app.is_job_running('RENDER')
r=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];h=r.pose.bones['Head']
h['Blink.L']=h['Blink.R']=.23
r.update_tag();bpy.context.view_layer.update();assert len(r.animation_data.drivers)==1957
p=out/'Character_An_eye_rest_pose_v483.blend';assert not p.exists()
bpy.ops.wm.save_as_mainfile(filepath=str(p))
(out/'report.json').write_text(json.dumps({'blink_controls':.23,'drivers':1957,'change':'pose only, no mesh or driver edits','review':'before, partial closure and full blink rendered and inspected; not likeness or animation acceptance'},indent=2))
print(str(p))
