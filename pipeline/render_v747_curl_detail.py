"""Resolve crown fibers without denoising; remote cropped render only."""
from pathlib import Path
import runpy

# Same reference-side camera and lighting; 1024 x 1024 crop at 8x
# preview pixel density. No changes to the checkpoint or groom geometry.
runpy.run_path(str(Path(__file__).with_name('render_v740_cloud_groom.py')),
               init_globals={'TAG': 'v747_curl_detail',
                             'VIEWS': ['reference_orientation'],
                             'RESOLUTION': (4096, 5120),
                             'BORDER': (.375, .625, .65, .85),
                             'SAMPLES': 128, 'ADAPTIVE_THRESHOLD': .02,
                             'DENOISE': False})
