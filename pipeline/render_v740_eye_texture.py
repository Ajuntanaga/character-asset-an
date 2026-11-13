"""Expose any baked eye detail on skin without changing eyelid geometry."""
from pathlib import Path
import runpy

renderer = Path(__file__).with_name('render_v740_cloud_groom.py')
for tag, excluded in [
    ('v740_eye_texture_control', []),
    ('v740_eye_texture_no_eyeballs', ['V737_EYE.L', 'V737_EYE.R',
                                    'V738_CORNEA.L', 'V738_CORNEA.R']),
]:
    runpy.run_path(str(renderer), init_globals={
        'TEXTURE_PATH': 'Character_An_photoreal_head_basecolor_v326.png',
        'TAG': tag, 'VIEWS': ['front'], 'SAMPLES': 24,
        'EXCLUDE_OBJECTS': excluded,
    })
