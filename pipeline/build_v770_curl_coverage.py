"""Broaden child-fiber spread without remaking the reviewed facial grooms."""
import hashlib
import json
import runpy
from pathlib import Path

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parent
OUT = Path(globals().get('OUTPUT_DIR', 'results'))
OUT.mkdir(parents=True, exist_ok=True)
head = bpy.data.objects['V740_NATIVE_FACE']
assert head.get('v769_hair_shading_trial')
assert not head.get('v770_curl_coverage_trial')
facial = ['V766_ASSET_' + part for part in ('BROWS', 'BEARD', 'MUSTACHE', 'LASHES')]

def fingerprint(name):
    data = bpy.data.objects[name].data
    points = np.empty((len(data.position_data), 3), dtype=np.float32)
    data.position_data.foreach_get('vector', points.ravel())
    uvs = np.empty((len(data.curves), 2), dtype=np.float32)
    data.attributes['surface_uv_coordinate'].data.foreach_get('vector', uvs.ravel())
    return hashlib.sha256(points.tobytes() + uvs.tobytes()).hexdigest()

before = {name: fingerprint(name) for name in facial}
scalp = bpy.data.objects['V766_ASSET_SCALP'].data
uvs_before = np.empty((len(scalp.curves), 2), dtype=np.float32)
scalp.attributes['surface_uv_coordinate'].data.foreach_get('vector', uvs_before.ravel())
runpy.run_path(str(ROOT / 'fit_v766_hair_assets.py'), init_globals={
    'SCALP_ONLY': True, 'TIP_ROOT_SPREAD': .65, 'RENDER': False, 'SAVE': False,
    'LIBRARY_DIR': globals().get('LIBRARY_DIR', 'results/hair-library'),
    'OUTPUT_DIR': str(OUT), 'REPORT_FILE': 'v770_curl_coverage_fit.json'})
assert before == {name: fingerprint(name) for name in facial}, 'Facial grooms changed'
scalp = bpy.data.objects['V766_ASSET_SCALP'].data
uvs_after = np.empty((len(scalp.curves), 2), dtype=np.float32)
scalp.attributes['surface_uv_coordinate'].data.foreach_get('vector', uvs_after.ravel())
assert np.array_equal(uvs_before, uvs_after), 'Scalp UV roots changed'
head['v770_curl_coverage_trial'] = True
report = {'facial_grooms_unchanged': True, 'scalp_uv_roots_unchanged': True,
          'tip_root_spread_before': .20, 'tip_root_spread_after': .65,
          'facial_groom_sha256': before}
if globals().get('RENDER', True):
    camera = json.loads((ROOT.parent / 'references/derived/photoreal_facebuilder_v1/fitted_camera_v761.json').read_text())
    base = {'EXTRA_OBJECTS': ['V766_ASSET_SCALP', *facial],
            'EXCLUDE_OBJECTS': ['V740_NATIVE_CURLS', 'V740_NATIVE_UNDERCOAT', 'V740_BROW_FIBERS', 'V740_BEARD_FIBERS'],
            'PRESERVE_MATERIALS': True, 'RESOLUTION': tuple(camera['size']),
            'SAMPLES': 128, 'ADAPTIVE_THRESHOLD': .02, 'DENOISE': True}
    for tag, settings in [
        ('v770_coverage', {'VIEWS': ['reference_orientation'], 'CAMERA_RECORD': camera}),
        ('v770_coverage_front', {'VIEWS': ['front']}),
        ('v770_coverage_motion', {'VIEWS': ['reference_orientation'], 'CAMERA_RECORD': camera,
                               'HEAD_TURN_DEGREES': 12., 'POSE': {'Blink.L': .65, 'Blink.R': .65}}),
    ]:
        runpy.run_path(str(ROOT / 'render_v740_cloud_groom.py'), init_globals={**base, **settings, 'TAG': tag})
output = Path(globals().get('SAVE_FILE', OUT / 'V770_curl_coverage_trial.blend')).resolve()
bpy.ops.wm.save_as_mainfile(filepath=str(output), compress=True)
report['checkpoint'] = str(output)
report['checkpoint_bytes'] = output.stat().st_size
(OUT / 'v770_curl_coverage_trial.json').write_text(json.dumps(report, indent=2))
print('CURL_COVERAGE_TRIAL_COMPLETE', json.dumps(report), flush=True)
