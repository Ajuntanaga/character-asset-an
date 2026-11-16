"""Reduce projected mustache root crowding while retaining donor strands and UVs."""
import hashlib
import json
import runpy
from pathlib import Path
import bpy
import numpy as np

ROOT = Path(__file__).resolve().parent
OUT = Path('results')
OUT.mkdir(exist_ok=True)
head = bpy.data.objects['V740_NATIVE_FACE']
rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
assert head.get('v775_surface_scalp_undercoat')
assert not head.get('v776_mustache_density')
assert len(head.data.shape_keys.key_blocks) == 52
assert len(rig.animation_data.drivers) == 1957
grooms = ['V766_ASSET_' + p for p in ('SCALP', 'BROWS', 'BEARD', 'MUSTACHE', 'LASHES')]
grooms += ['V775_SCALP_UNDERCOAT']

def read_curves(obj):
    data = obj.data
    points = np.empty((len(data.position_data), 3), np.float32)
    data.position_data.foreach_get('vector', points.ravel())
    uvs = np.empty((len(data.curves), 2), np.float32)
    data.attributes['surface_uv_coordinate'].data.foreach_get('vector', uvs.ravel())
    radii = np.empty(len(points), np.float32)
    data.attributes['radius'].data.foreach_get('value', radii)
    counts = np.array([len(c.points) for c in data.curves], dtype=np.int32)
    return points, uvs, radii, counts


def fingerprint(name):
    return hashlib.sha256(b''.join(a.tobytes() for a in read_curves(bpy.data.objects[name]))).hexdigest()


before = {name: fingerprint(name) for name in grooms}
mustache = bpy.data.objects['V766_ASSET_MUSTACHE']
points, uvs, radii, counts = read_curves(mustache)
starts = np.r_[0, np.cumsum(counts)]
roots = points[starts[:-1]]
rng = np.random.default_rng(776)
# Choose one existing root per cell, retaining real surface and UV coordinates.
# Shuffling avoids favoring the ordered donor's dense central sections.
order = rng.permutation(len(counts))
cells = np.floor(roots[order]/.0007).astype(np.int32)
_, first = np.unique(cells, axis=0, return_index=True)
selected = np.sort(order[first])
new_points, new_radii = [], []
for index in selected:
    path = points[starts[index]:starts[index+1]].copy()
    # Scale towards the root so the shortened strand follows its original shape.
    length = np.linalg.norm(np.diff(path, axis=0), axis=1).sum()
    factor = min(1., rng.uniform(.0022, .0034)/max(length, 1e-9))
    path = path[0]+(path-path[0])*factor
    new_points.append(path)
    new_radii.append(radii[starts[index]:starts[index+1]]*(.000032/.000038))
data = bpy.data.hair_curves.new('V776_DENSITY_BALANCED_MUSTACHE')
data.add_curves(counts[selected].tolist())
data.set_types(type='CATMULL_ROM')
data.position_data.foreach_set('vector', np.concatenate(new_points).ravel())
data.attributes.new('radius', 'FLOAT', 'POINT').data.foreach_set('value', np.concatenate(new_radii))
data.attributes.new('surface_uv_coordinate', 'FLOAT2', 'CURVE').data.foreach_set('vector', uvs[selected].ravel())
data.surface = head; data.surface_uv_map = 'UVMap'
data.surface_collision_distance = .00015
for material in mustache.data.materials:
    data.materials.append(material)
old_data = mustache.data
mustache.data = data
if old_data.users == 0:
    bpy.data.hair_curves.remove(old_data)
assert all(fingerprint(name) == before[name] for name in grooms if name != mustache.name)
new = read_curves(mustache)
assert np.array_equal(new[1], uvs[selected])
assert np.array_equal(new[0][np.r_[0, np.cumsum(new[3])[:-1]]], roots[selected])
head['v776_mustache_density'] = True
report = {'source': bpy.data.filepath, 'mustache_curves_before': len(counts),
          'mustache_curves_after': len(selected), 'root_cell_m': .0007,
          'strand_length_target_m': [.0022, .0034], 'root_radius_m': .000032,
          'retained_roots_and_uvs_unchanged': True, 'other_five_grooms_unchanged': True,
          'face_shape_keys': 52, 'rig_drivers': 1957,
          'license': 'licenses/hair-asset-sources.md'}
(OUT / 'v776_mustache_density.json').write_text(json.dumps(report, indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str((OUT / 'V776_mustache_trial.blend').resolve()), compress=True)

camera = json.loads((ROOT.parent / 'references/derived/photoreal_facebuilder_v1/fitted_camera_v761.json').read_text())
base = {'EXTRA_OBJECTS': grooms,
        'EXCLUDE_OBJECTS': ['V740_NATIVE_CURLS', 'V740_NATIVE_UNDERCOAT', 'V740_BROW_FIBERS', 'V740_BEARD_FIBERS'],
        'PRESERVE_MATERIALS': True, 'RESOLUTION': tuple(camera['size']),
        'SAMPLES': 128, 'ADAPTIVE_THRESHOLD': .02, 'DENOISE': True}
for tag, view, options in [
        ('v776_mustache', 'front', {}),
        ('v776_mustache', 'reference_orientation', {'CAMERA_RECORD': camera}),
        ('v776_motion', 'reference_orientation', {'CAMERA_RECORD': camera, 'HEAD_TURN_DEGREES': 12.,
                                                  'POSE': {'Blink.L': .65, 'Blink.R': .65}})]:
    runpy.run_path(str(ROOT / 'render_v740_cloud_groom.py'), init_globals={
        **base, **options, 'TAG': tag, 'VIEWS': [view]})
print('MUSTACHE_DENSITY_TRIAL_COMPLETE', flush=True)
