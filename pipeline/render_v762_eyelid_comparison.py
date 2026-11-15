"""Preview partial native blinks; do not alter the neutral asset or save a scene."""
import json
import runpy
from pathlib import Path
import bpy
root = Path(__file__).resolve().parents[1]
record = json.loads((root/'references/derived/photoreal_facebuilder_v1/fitted_camera_v761.json').read_text())
rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
ctrl = rig.pose.bones['Head']
prior = {name: ctrl[name] for name in ('Blink.L', 'Blink.R')}
trials = []
try:
    for label, amount in [('relaxed15', .15), ('relaxed30', .30)]:
        for name in prior:
            ctrl[name] = amount
        rig.update_tag(refresh={'OBJECT'})
        bpy.context.view_layer.update()
        keys = bpy.data.objects['V740_NATIVE_FACE'].data.shape_keys.key_blocks
        evaluated = {name: keys[name].value for name in ('eyeBlinkLeft', 'eyeBlinkRight')}
        assert all(abs(value - amount) < 1e-4 for value in evaluated.values()), evaluated
        runpy.run_path(str(Path(__file__).with_name('render_v740_cloud_groom.py')),
                      init_globals={'TAG': 'v762_' + label, 'VIEWS': ['reference_orientation'],
                                    'CAMERA_RECORD': record, 'PRESERVE_MATERIALS': True,
                                    'RESOLUTION': tuple(record['size']), 'SAMPLES': 32})
        trials.append({'label': label, 'amount': amount, 'evaluated_keys': evaluated})
finally:
    for name, value in prior.items():
        ctrl[name] = value
    rig.update_tag(refresh={'OBJECT'})
    bpy.context.view_layer.update()
Path('results/v762_eyelid_comparison.json').write_text(json.dumps(
    {'trials': trials, 'checkpoint_saved': False, 'controls_restored': dict(prior)}, indent=2))
