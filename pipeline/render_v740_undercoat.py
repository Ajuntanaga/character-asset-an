"""Isolate the filling layer to distinguish coverage from curl silhouette defects."""
from pathlib import Path
import runpy

runpy.run_path(str(Path(__file__).with_name('render_v740_cloud_groom.py')),
               init_globals={'TAG': 'v740_undercoat', 'VIEWS': ['three_quarter'],
                             'EXCLUDE_OBJECTS': ['V740_NATIVE_CURLS']})
