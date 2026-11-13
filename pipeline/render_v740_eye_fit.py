"""Compare the inherited eye fit allowance without editing the saved checkpoint."""
from pathlib import Path
import json
import runpy
import bpy
from mathutils import Matrix

# Source: local_diagnostics/face_v736/eye_fit.json, used by V737 construction.
radii = {'L': .01791399355072844, 'R': .017762301224457426}
eyes = {side: bpy.data.objects['V737_EYE.' + side] for side in radii}
original = {side: eye.matrix_basis.copy() for side, eye in eyes.items()}
for side, eye in eyes.items():
    assert bpy.data.objects['V738_CORNEA.' + side].parent == eye
properties = ['JawOpen', 'Blink.L', 'Blink.R', 'BrowInnerUp',
              'BrowDown.L', 'BrowDown.R', 'BrowOuterUp.L', 'BrowOuterUp.R',
              'Smile.L', 'Smile.R', 'MouthPucker']
renderer = Path(__file__).with_name('render_v740_cloud_groom.py')
records = []
try:
    for variant in ['control', 'without_allowance']:
        factors = {s: (r / (r + .0006) if variant == 'without_allowance' else 1.)
                   for s, r in radii.items()}
        for side, eye in eyes.items():
            f = factors[side]
            eye.matrix_basis = original[side] @ Matrix.Diagonal((f, f, f, 1.))
        bpy.context.view_layer.update()
        for expression in ['rest', 'blink']:
            pose = dict.fromkeys(properties, 0.)
            if expression == 'blink':
                pose.update({'Blink.L': 1., 'Blink.R': 1.})
            tag = 'v740_eye_fit_' + variant + '_' + expression
            runpy.run_path(str(renderer), init_globals={
                'TEXTURE_PATH': 'Character_An_photoreal_head_basecolor_v326.png',
                'POSE': pose, 'TAG': tag, 'VIEWS': ['front'], 'SAMPLES': 24,
            })
            records.append({'variant': variant, 'expression': expression,
                            'relative_scale': factors, 'image': tag + '_front.png'})
finally:
    for side, eye in eyes.items():
        eye.matrix_basis = original[side]
    bpy.context.view_layer.update()
Path('results/eye_fit_comparison.json').write_text(json.dumps({
    'cases': records, 'scope': 'Static eye fit comparison; requires visual review. '
    'No eyelid, gaze, or saved checkpoint modification; no animation acceptance.',
}, indent=2))
