from pathlib import Path
import bpy,json
ROOT=Path(__file__).resolve().parents[1]
assert not bpy.app.is_job_running('RENDER')
rig=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];assert len(rig.animation_data.drivers)==1957
for side in ('L','R'):
 assert rig.pose.bones['Head']['Blink.'+side]==0
 assert abs(bpy.data.objects['V374_EYE.'+side].data.shape_keys.key_blocks['Dilation'].value-.9)<1e-5
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'production_v394_eyelashes/Character_An_eyelashes_v394.blend'),compress=True)
print(json.dumps({'saved':bpy.data.filepath,'rig_drivers':len(rig.animation_data.drivers),'neutral':True}))
