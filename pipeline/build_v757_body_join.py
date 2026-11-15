"""Cloud body/head assembly trial; preserve originals and reject incompatible rigs."""
from pathlib import Path
import json
import runpy
import sys
import bpy
sys.path.insert(0, str(Path(__file__).resolve().parent))
from mask_v757_legacy_head import build

rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
body_name = 'V416_BODY_CLEAN_JOIN'
assert bpy.data.objects.get(body_name) is None, 'Unexpected existing body'
with bpy.data.libraries.load(str(Path('scenes/current-v544.blend').resolve()), link=False) as (source, target):
    assert body_name in source.objects
    target.objects = [body_name]
body = target.objects[0]
bpy.context.scene.collection.objects.link(body)
armatures = [m for m in body.modifiers if m.type == 'ARMATURE']
assert len(armatures) == 1
old = armatures[0].object
assert old and old != rig
errors = {}
for bone in old.data.bones:
    if not bone.use_deform:
        continue
    assert bone.name in rig.data.bones, bone.name
    other = rig.data.bones[bone.name]
    errors[bone.name] = max(abs(bone.matrix_local[i][j]-other.matrix_local[i][j]) for i in range(4) for j in range(4))
assert max(errors.values()) < 2e-5, errors
assert max(abs(old.matrix_world[i][j]-rig.matrix_world[i][j]) for i in range(4) for j in range(4)) < 2e-5
world = body.matrix_world.copy()
if body.parent:
    assert body.parent == old and body.parent_type == 'OBJECT'
    body.parent = rig
    body.matrix_world = world
armatures[0].object = rig
report = build(body)
body.hide_render = False
body.hide_viewport = False
body.hide_set(False)
report['rig_rest_max_error'] = max(errors.values())
report['status'] = 'BODY_JOIN_TRIAL_REQUIRES_RENDER_REVIEW'
Path('results/v757-body-join.json').write_text(json.dumps(report, indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(Path('results/V757_body_join_trial.blend').resolve()), compress=True)
runpy.run_path(str(Path(__file__).with_name('render_v740_cloud_groom.py')), init_globals={
    'TAG': 'v757_body_join', 'EXTRA_OBJECTS': [body.name], 'PRESERVE_MATERIALS': True,
    'CAMERA_TARGET': (0., 0., 1.45), 'ORTHO_SCALE': .85,
    'VIEWS': ['front', 'three_quarter'], 'SAMPLES': 16,
})

# Test the actual clothed assembly: isolated neck turns cannot expose collar intersections.
for label, degrees in [('left', 25.), ('right', -25.)]:
    runpy.run_path(str(Path(__file__).with_name('render_v740_cloud_groom.py')), init_globals={
        'TAG': 'v757_body_join_' + label,
        'EXTRA_OBJECTS': [body.name], 'PRESERVE_MATERIALS': True,
        'CAMERA_TARGET': (0., 0., 1.52), 'ORTHO_SCALE': .58,
        'VIEWS': ['front', 'three_quarter'], 'SAMPLES': 16,
        'HEAD_TURN_DEGREES': degrees,
    })
