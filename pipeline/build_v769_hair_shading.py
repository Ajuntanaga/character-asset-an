"""Compare a restrained hair highlight response on the saved upper-lid trial."""
import json
import runpy
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parent
OUT = Path(globals().get('OUTPUT_DIR', 'results'))
OUT.mkdir(parents=True, exist_ok=True)
head = bpy.data.objects['V740_NATIVE_FACE']
rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
assert head.get('v768_upper_lid_trial'), 'Start from the reviewed V768 lids'
assert not head.get('v769_hair_shading_trial'), 'Do not apply twice'
assert len(head.data.shape_keys.key_blocks) == 52
assert len(rig.animation_data.drivers) == 1957
keys_before = {key.name: float(key.value) for key in head.data.shape_keys.key_blocks}
material = bpy.data.materials['V766_DARK_NATURAL_HAIR']
shader = next(node for node in material.node_tree.nodes
              if node.bl_idname == 'ShaderNodeBsdfHairPrincipled')
assert shader.model == 'CHIANG' and shader.parametrization == 'MELANIN'
changes = {'Roughness': .42, 'Radial Roughness': .45, 'Coat': 0., 'Random Color': 0.}
report = {'source': bpy.data.filepath, 'revision': 'restrained hair highlights',
          'changes': {}, 'preserved_shape_keys': 52, 'preserved_rig_drivers': 1957,
          'geometry_changed': False}
for name, value in changes.items():
    report['changes'][name] = {'before': float(shader.inputs[name].default_value), 'after': value}
    shader.inputs[name].default_value = value
head['v769_hair_shading_trial'] = True
bpy.context.view_layer.update()

if globals().get('RENDER', True):
    camera = json.loads((ROOT.parent / 'references/derived/photoreal_facebuilder_v1/fitted_camera_v761.json').read_text())
    base = {'EXTRA_OBJECTS': ['V766_ASSET_' + name for name in ('SCALP', 'BROWS', 'BEARD', 'MUSTACHE', 'LASHES')],
            'EXCLUDE_OBJECTS': ['V740_NATIVE_CURLS', 'V740_NATIVE_UNDERCOAT', 'V740_BROW_FIBERS', 'V740_BEARD_FIBERS'],
            'PRESERVE_MATERIALS': True, 'RESOLUTION': tuple(camera['size']),
            'SAMPLES': 128, 'ADAPTIVE_THRESHOLD': .02, 'DENOISE': True}
    for tag, settings in [
        ('v769_hair', {'VIEWS': ['reference_orientation'], 'CAMERA_RECORD': camera}),
        ('v769_hair_front', {'VIEWS': ['front']}),
        ('v769_hair_motion', {'VIEWS': ['reference_orientation'], 'CAMERA_RECORD': camera,
                              'HEAD_TURN_DEGREES': 12., 'POSE': {'Blink.L': .65, 'Blink.R': .65}}),
    ]:
        runpy.run_path(str(ROOT / 'render_v740_cloud_groom.py'), init_globals={**base, **settings, 'TAG': tag})
assert {key.name: float(key.value) for key in head.data.shape_keys.key_blocks} == keys_before
output = Path(globals().get('SAVE_FILE', OUT / 'V769_hair_shading_trial.blend')).resolve()
bpy.ops.wm.save_as_mainfile(filepath=str(output), compress=True)
report['checkpoint'] = str(output)
report['checkpoint_bytes'] = output.stat().st_size
(OUT / 'v769_hair_shading_trial.json').write_text(json.dumps(report, indent=2))
print('HAIR_SHADING_TRIAL_COMPLETE', json.dumps(report), flush=True)
