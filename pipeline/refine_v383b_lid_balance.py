"""Ease the visually over-narrow V383 lids halfway toward the prior opening."""
import json
from pathlib import Path
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
assert not bpy.app.is_job_running('RENDER')
body = bpy.data.objects['V357_TRIPO_CHARACTER_BODY_BOUND']
assert body.get('V383_eye_opening_applied')
assert not body.get('V383b_lid_balance')
keys = body.data.shape_keys.key_blocks
backup = json.loads((ROOT/'production_v383_face_detail/before_relaxed_lids.json').read_text())
for side, old_keys in backup.items():
    basis = keys['Basis']
    ids = [int(v) for v in old_keys['Basis']]
    deltas = {i:(Vector(old_keys['Basis'][str(i)])-basis.data[i].co)*.5 for i in ids}
    margin = bpy.data.objects['V369_LID_MARGIN.'+side]
    margin_basis = margin.data.shape_keys.key_blocks['Basis']
    for i in range(64):
        center = sum((margin_basis.data[i*6+k].co for k in range(6)),Vector())/6
        nearest = min(ids,key=lambda v:(basis.data[v].co-center).length_squared)
        for k in range(6):
            margin_basis.data[i*6+k].co += deltas[nearest]
    for key in keys:
        if key.name == 'Blink.'+side:
            continue
        for v, co in old_keys[key.name].items():
            key.data[int(v)].co = key.data[int(v)].co.lerp(Vector(co),.5)
    margin.data.update()
body['V383b_lid_balance'] = True
body.data.update()
rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
rig.pose.bones['Head']['Blink.L'] = 0.
rig.pose.bones['Head']['Blink.R'] = 0.
rig.update_tag()
bpy.context.view_layer.update()
assert len(rig.animation_data.drivers) == 1957
print('V383b: half of V383 lid narrowing; closed targets retained; 1957 drivers')
