"""Render original and trial eyelid atlases at rest and blink; never save the scene."""
from pathlib import Path
import hashlib
import runpy

original = Path('Character_An_photoreal_head_basecolor_v326.png')
trial = Path('references/derived/eyelid_albedo_v745/Character_An_eyelid_albedo_TRIAL_v745.png')
assert hashlib.sha256(trial.read_bytes()).hexdigest() == '1b8cb0746c98547e78f9b7872a1b6b2a6dc4d71031a928ece7b659f2c3bb2802'
renderer = Path(__file__).with_name('render_v740_cloud_groom.py')
source_name = original.name
for label, texture in [('original', original), ('trial', trial)]:
    for pose, blink in [('rest', 0.), ('blink', 1.)]:
        runpy.run_path(str(renderer), init_globals={
            'TEXTURE_PATH': str(texture),
            'TEXTURE_SOURCE_NAME': source_name,
            'POSE': {'Blink.L': blink, 'Blink.R': blink},
            'TAG': 'v745_eyelid_' + label + '_' + pose,
            'VIEWS': ['front'], 'SAMPLES': 24,
        })
        source_name = texture.name
