"""Review approximate donor correspondence fit with original camera intrinsics."""
import json
import runpy
from pathlib import Path
root = Path(__file__).resolve().parents[1]
record = json.loads((root/'references/derived/photoreal_facebuilder_v1/fitted_camera_v761.json').read_text())
runpy.run_path(str(Path(__file__).with_name('render_v740_cloud_groom.py')),
              init_globals={'TAG':'v761_fitted_camera', 'VIEWS':['reference_orientation'],
                            'CAMERA_RECORD':record, 'PRESERVE_MATERIALS':True,
                            'RESOLUTION':tuple(record['size']), 'SAMPLES':32})
