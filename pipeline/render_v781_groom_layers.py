"""Isolate V779 scalp layers without changing the production checkpoint."""
import json
from pathlib import Path
import runpy

import bpy

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'results'
OUT.mkdir(exist_ok=True)
camera = json.loads((ROOT / 'references/derived/photoreal_facebuilder_v1/fitted_camera_v761.json').read_text())
legacy = ['V740_NATIVE_CURLS', 'V740_NATIVE_UNDERCOAT',
          'V740_BROW_FIBERS', 'V740_BEARD_FIBERS']
grooms = ['V766_ASSET_' + part for part in ('SCALP', 'BROWS', 'BEARD', 'MUSTACHE', 'LASHES')]
grooms += ['V775_SCALP_UNDERCOAT', 'V779_TEMPLE_HAIR']
variants = {
    'full': [],
    'short_layers': ['V766_ASSET_SCALP'],
    'outer_curls': ['V775_SCALP_UNDERCOAT', 'V779_TEMPLE_HAIR'],
}
report = {'source': Path(bpy.data.filepath).name,
          'scope': 'Scalp layer isolation only; no scene or groom changes saved.',
          'variants': {}}
for label, exclusions in variants.items():
    tag = 'v781_' + label
    runpy.run_path(str(ROOT / 'pipeline/render_v740_cloud_groom.py'), init_globals={
        'PRESERVE_MATERIALS': True,
        'EXTRA_OBJECTS': grooms,
        'EXCLUDE_OBJECTS': legacy + exclusions,
        'CAMERA_RECORD': camera,
        'VIEWS': ['reference_orientation'],
        'RESOLUTION': tuple(camera['size']),
        'BORDER': (.10, .85, .57, .98),
        'SAMPLES': 128,
        'ADAPTIVE_THRESHOLD': .015,
        'DENOISE': True,
        'TAG': tag,
    })
    rendered = json.loads((OUT / (tag + '_render_report.json')).read_text())
    assert rendered['production_unchanged'] and rendered['head_basis_restored']
    assert rendered['rig_drivers'] == 1957
    report['variants'][label] = {key: rendered[key] for key in (
        'renders', 'excluded_objects', 'render_settings', 'production_unchanged',
        'head_basis_restored', 'rig_drivers')}
    report['variants'][label]['bytes'] = sum(Path(p).stat().st_size for p in rendered['renders'])
(OUT / 'v781_layer_review.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report))
