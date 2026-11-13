"""Resolve brows and moustache without denoising; remote diagnostic only."""
from pathlib import Path
import runpy

# Four times the neutral preview pixel density, cropped to brows through lips.
# Preserve its clay material and lighting so fiber visibility is comparable.
runpy.run_path(str(Path(__file__).with_name('render_v740_cloud_groom.py')),
              init_globals={'TAG': 'v748_facial_detail',
                            'VIEWS': ['front'],
                            'RESOLUTION': (2048, 2560),
                            'BORDER': (.25, .75, .28, .62),
                            'SAMPLES': 128, 'ADAPTIVE_THRESHOLD': .02,
                            'DENOISE': False})
