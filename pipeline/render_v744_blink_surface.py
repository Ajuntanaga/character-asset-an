"""Isolate closed-lid surface from eye intersection; no checkpoint edits."""
from pathlib import Path
import runpy
renderer = Path(__file__).with_name('render_v740_cloud_groom.py')
for variant, excluded in [('eyes', []), ('no_eyes', ['V737_EYE.L', 'V737_EYE.R', 'V738_CORNEA.L', 'V738_CORNEA.R'])]:
    runpy.run_path(str(renderer), init_globals={
        'POSE': {'Blink.L': 1., 'Blink.R': 1.},
        'EXCLUDE_OBJECTS': excluded,
        'TAG': 'v744_blink_surface_' + variant,
        'VIEWS': ['front'], 'SAMPLES': 24,
    })
