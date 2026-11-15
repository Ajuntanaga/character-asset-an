"""Matched target-plane framing; diagnostic only, not a reference camera fit."""
from pathlib import Path
import runpy

for projection in ('ORTHO', 'PERSP'):
    runpy.run_path(str(Path(__file__).with_name('render_v740_cloud_groom.py')),
                  init_globals={'TAG': 'v759_' + projection.lower(),
                                'VIEWS': ['reference_orientation'],
                                'CAMERA_PROJECTION': projection,
                                'CAMERA_LENS': 50.0,
                                'PRESERVE_MATERIALS': True,
                                'SAMPLES': 24})
