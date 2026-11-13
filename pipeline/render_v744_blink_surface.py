"""Compare textured and neutral closed lids, with/without eyes; no scene save."""
from pathlib import Path
import runpy

renderer = Path(__file__).with_name('render_v740_cloud_groom.py')
# Textured passes must precede clay: the preview renderer replaces material slots.
for material in ['textured', 'neutral']:
    for variant, excluded in [
        ('eyes', []),
        ('no_eyes', ['V737_EYE.L', 'V737_EYE.R', 'V738_CORNEA.L', 'V738_CORNEA.R']),
    ]:
        options = {
            'POSE': {'Blink.L': 1., 'Blink.R': 1.},
            'EXCLUDE_OBJECTS': excluded,
            'TAG': 'v744_blink_surface_' + material + '_' + variant,
            'VIEWS': ['front'], 'SAMPLES': 24,
        }
        if material == 'textured':
            options['TEXTURE_PATH'] = 'Character_An_photoreal_head_basecolor_v326.png'
        runpy.run_path(str(renderer), init_globals=options)
