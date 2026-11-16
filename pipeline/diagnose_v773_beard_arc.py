"""Isolate skin, strands and deformation behind the visible beard arc."""
import json
import runpy
from pathlib import Path
import bpy
import numpy as np

ROOT = Path(__file__).resolve().parent
OUT = Path('results')
OUT.mkdir(exist_ok=True)
head = bpy.data.objects['V740_NATIVE_FACE']
assert head.get('v769_hair_shading_trial')
grooms = ['V766_ASSET_' + p for p in ('SCALP', 'BROWS', 'BEARD', 'MUSTACHE', 'LASHES')]
old = ['V740_NATIVE_CURLS', 'V740_NATIVE_UNDERCOAT', 'V740_BROW_FIBERS', 'V740_BEARD_FIBERS']
base = {'EXTRA_OBJECTS': grooms, 'EXCLUDE_OBJECTS': old,
        'PRESERVE_MATERIALS': True, 'RESOLUTION': (645, 813),
        'SAMPLES': 128, 'ADAPTIVE_THRESHOLD': .02, 'DENOISE': True, 'VIEWS': ['front']}

def render(tag, **options):
    runpy.run_path(str(ROOT / 'render_v740_cloud_groom.py'), init_globals={**base, **options, 'TAG': tag})

# Read matching raw and evaluated curve positions before any material changes.
beard = bpy.data.objects['V766_ASSET_BEARD']
bpy.context.view_layer.update()
evaluated = beard.evaluated_get(bpy.context.evaluated_depsgraph_get())
points = np.empty((len(beard.data.position_data), 3), np.float32)
beard.data.position_data.foreach_get('vector', points.ravel())
eval_points = np.empty((len(evaluated.data.position_data), 3), np.float32)
evaluated.data.position_data.foreach_get('vector', eval_points.ravel())
counts = np.array([len(c.points) for c in beard.data.curves])
starts = np.r_[0, np.cumsum(counts)[:-1]]
report = {'raw_points': len(points), 'evaluated_points': len(eval_points),
          'beard_curves': len(counts), 'source': bpy.data.filepath}
if points.shape == eval_points.shape:
    distance = np.linalg.norm(points - eval_points, axis=1)
    report['deformation_distance_percentiles_m'] = np.percentile(distance, [0,50,95,99,100]).tolist()
    np.savez_compressed(OUT / 'v773_beard_roots.npz', raw=points[starts], evaluated=eval_points[starts])
render('v773_textured_without_facial_hair', EXCLUDE_OBJECTS=old+grooms[1:4])
render('v773_clay_with_facial_hair', PRESERVE_MATERIALS=False)
# Determine whether the surface attachment, rather than fitted paths, creates the arc.
mods = [(m, m.show_render) for name in grooms[1:4] for m in bpy.data.objects[name].modifiers]
try:
    for m, _ in mods:
        m.show_render = False
    render('v773_clay_without_facial_deformation')
finally:
    for m, visible in mods:
        m.show_render = visible
(OUT / 'v773_arc_isolation.json').write_text(json.dumps(report, indent=2))
print('BEARD_ARC_ISOLATION_COMPLETE', flush=True)
