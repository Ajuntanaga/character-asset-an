import bpy,json
from pathlib import Path
assert not bpy.app.is_job_running('RENDER')
rig=bpy.data.objects['V357_CLOUDRIG_CONTROLS']
body=bpy.data.objects['V357_TRIPO_CHARACTER_BODY_BOUND']
fibers=bpy.data.objects['V395_BEARD_FIBERS']
head=rig.pose.bones['Head']
report={}
for control in ('JawOpen','Smile.L','Smile.R'):
 old=head[control]
 head[control]=.6
 rig.update_tag();bpy.context.view_layer.update()
 a=body.data.shape_keys.key_blocks[control].value
 b=fibers.data.shape_keys.key_blocks[control].value
 report[control]={'body':a,'hair':b}
 assert abs(a-b)<1e-6 and a>.1
 head[control]=old
 rig.update_tag();bpy.context.view_layer.update()
assert len(rig.animation_data.drivers)==1957
out=Path(__file__).resolve().parents[1]/'production_v395_facial_hair'
(out/'expression_check.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
