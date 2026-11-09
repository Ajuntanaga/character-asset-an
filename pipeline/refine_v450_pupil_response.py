"""Reduce excessive resting pupil dilation without changing globe/lid geometry."""
from pathlib import Path
import bpy,json
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'production_v450_pupil_response';OUT.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
assert bpy.data.filepath.endswith('Character_An_swept_curls_v449.blend')
rig=bpy.data.objects['V357_CLOUDRIG_CONTROLS']
assert len(rig.animation_data.drivers)==1957
report={}
for side in ('L','R'):
 eye=bpy.data.objects['V374_EYE.'+side]
 key=eye.data.shape_keys.key_blocks['Dilation']
 report[side]={'before':key.value,'after':.35}
 key.value=.35
 eye.data.update()
bpy.context.view_layer.update()
(OUT/'changes.json').write_text(json.dumps(report,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Character_An_pupil_response_v450.blend'),compress=True)
print(json.dumps(report))
