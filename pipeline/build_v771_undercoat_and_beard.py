"""Review a short curl undercoat, then soften the imported beard boundary."""
import hashlib
import json
import runpy
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parent
OUT = Path('results')
OUT.mkdir(exist_ok=True)
head = bpy.data.objects['V740_NATIVE_FACE']
rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
assert head.get('v769_hair_shading_trial')
assert not head.get('v770_curl_coverage_trial')
assert bpy.data.objects.get('V771_CURL_UNDERCOAT') is None
assert len(head.data.shape_keys.key_blocks) == 52
assert len(rig.animation_data.drivers) == 1957
grooms = ['V766_ASSET_' + p for p in ('SCALP', 'BROWS', 'BEARD', 'MUSTACHE', 'LASHES')]


def read_curves(obj):
    data = obj.data
    points = np.empty((len(data.position_data), 3), dtype=np.float32)
    data.position_data.foreach_get('vector', points.ravel())
    uvs = np.empty((len(data.curves), 2), dtype=np.float32)
    data.attributes['surface_uv_coordinate'].data.foreach_get('vector', uvs.ravel())
    radii = np.empty(len(points), dtype=np.float32)
    data.attributes['radius'].data.foreach_get('value', radii)
    counts = np.array([len(c.points) for c in data.curves], dtype=np.int32)
    return points, uvs, radii, counts


def fingerprint(name):
    return hashlib.sha256(b''.join(a.tobytes() for a in read_curves(bpy.data.objects[name]))).hexdigest()


def install(name, template, points, uvs, radii, counts):
    assert np.isfinite(points).all() and len(points) == sum(counts)
    data = bpy.data.hair_curves.new(name)
    data.add_curves(counts.tolist())
    data.set_types(type='CATMULL_ROM')
    data.position_data.foreach_set('vector', points.ravel())
    data.attributes.new('radius', 'FLOAT', 'POINT').data.foreach_set('value', radii)
    data.attributes.new('surface_uv_coordinate', 'FLOAT2', 'CURVE').data.foreach_set('vector', uvs.ravel())
    data.surface = head
    data.surface_uv_map = 'UVMap'
    data.surface_collision_distance = .00015
    for mat in template.data.materials:
        data.materials.append(mat)
    obj = template.copy()
    obj.data = data
    obj.name = name
    for collection in template.users_collection:
        collection.objects.link(obj)
    obj.hide_render = False
    obj.hide_viewport = False
    obj['adaptation'] = 'Short donor curls beneath V769, or density-feathered Einar beard; UV attachment retained'
    return obj


camera = json.loads((ROOT.parent / 'references/derived/photoreal_facebuilder_v1/fitted_camera_v761.json').read_text())


def render(tag, motion=False):
    base = {'EXTRA_OBJECTS': [*grooms, 'V771_CURL_UNDERCOAT'],
            'EXCLUDE_OBJECTS': ['V740_NATIVE_CURLS', 'V740_NATIVE_UNDERCOAT', 'V740_BROW_FIBERS', 'V740_BEARD_FIBERS'],
            'PRESERVE_MATERIALS': True, 'RESOLUTION': tuple(camera['size']),
            'SAMPLES': 128, 'ADAPTIVE_THRESHOLD': .02, 'DENOISE': True}
    settings = [('reference_orientation', {'CAMERA_RECORD': camera}), ('front', {})]
    if motion:
        settings.append(('motion', {'CAMERA_RECORD': camera, 'HEAD_TURN_DEGREES': 12.,
                                    'POSE': {'Blink.L': .65, 'Blink.R': .65}}))
    for view, options in settings:
        runpy.run_path(str(ROOT / 'render_v740_cloud_groom.py'), init_globals={
            **base, **options, 'TAG': tag + ('_motion' if view == 'motion' else ''),
            'VIEWS': ['reference_orientation' if view == 'motion' else view]})


before = {name: fingerprint(name) for name in grooms}
scalp = bpy.data.objects['V766_ASSET_SCALP']
points, uvs, radii, counts = read_curves(scalp)
assert np.all(counts == 23)
paths = points.reshape(-1, 23, 3).astype(np.float64)
roots = paths[:, 0].copy()
lengths = np.linalg.norm(np.diff(paths, axis=1), axis=2).sum(axis=1)
assert np.isfinite(lengths).all() and np.all(lengths > 0)
rng = np.random.default_rng(771)
target_lengths = rng.uniform(.003, .006, len(paths))
paths = roots[:, None] + (paths - roots[:, None]) * (target_lengths / lengths)[:, None, None]
# Keep the short curled layer outside each root's native skin tangent.
mesh = head.data
coords = [p.co[:] for p in mesh.shape_keys.key_blocks['Basis'].data]
tree = BVHTree.FromPolygons(coords, [p.vertices[:] for p in mesh.polygons])
normals = np.asarray([tree.find_nearest(Vector(p))[1][:] for p in roots])
height = np.einsum('npi,ni->np', paths - roots[:, None], normals)
paths += np.maximum(.00008 - height, 0.)[:, :, None] * normals[:, None]
under_radii = np.tile(.000035 * (1 - .94 * np.linspace(0, 1, 23)**2), len(paths)).astype(np.float32)
undercoat = install('V771_CURL_UNDERCOAT', scalp, paths.reshape(-1, 3).astype(np.float32),
                    uvs, under_radii, counts)
undercoat['asset_source_and_license'] = scalp['asset_source_and_license']
assert before == {name: fingerprint(name) for name in grooms}
head['v771_short_undercoat_trial'] = True
render('v771_undercoat')
bpy.ops.wm.save_as_mainfile(filepath=str((OUT / 'V771_short_undercoat_trial.blend').resolve()), compress=True)
report = {'source': 'V769_hair_shading_trial.blend', 'foreground_grooms_unchanged': True,
          'undercoat_curves': len(counts), 'undercoat_arc_length_target_m': [.003, .006],
          'undercoat_root_radius_m': .000035, 'undercoat_uv_roots_equal_scalp': True}
(OUT / 'v771_undercoat_trial.json').write_text(json.dumps(report, indent=2))

# The upper beard edge was a binary cutoff. Thin and shorten its last 7 mm
# deterministically while keeping every retained root at its established UV.
beard = bpy.data.objects['V766_ASSET_BEARD']
points, uvs, radii, counts = read_curves(beard)
offsets = np.r_[0, np.cumsum(counts)]
roots = points[offsets[:-1]]
edge = np.interp(abs(roots[:, 0]), [0., .025, .035, .050, .080], [1.562, 1.565, 1.585, 1.609, 1.640])
fade = np.clip((edge - roots[:, 2]) / .007, 0, 1)
fade = fade * fade * (3 - 2 * fade)
keep = np.random.default_rng(772).random(len(counts)) < fade
retained = np.flatnonzero(keep)
assert len(retained) > 20
paths, kept_radii = [], []
for i in retained:
    first, last = offsets[i:i+2]
    paths.append(roots[i] + (points[first:last] - roots[i]) * (.4 + .6 * fade[i]))
    kept_radii.append(radii[first:last])
replacement = install('V772_FEATHERED_BEARD', beard, np.concatenate(paths).astype(np.float32),
                      uvs[keep], np.concatenate(kept_radii), counts[keep])
old_data = beard.data
bpy.data.objects.remove(beard, do_unlink=True)
if old_data.users == 0:
    bpy.data.hair_curves.remove(old_data)
replacement.name = 'V766_ASSET_BEARD'
replacement.data.name = 'V772_FEATHERED_BEARD'
assert all(fingerprint(name) == before[name] for name in grooms if name != replacement.name)
assert np.array_equal(read_curves(replacement)[1], uvs[keep])
head['v772_beard_edge_trial'] = True
render('v772_beard_edge', motion=True)
assert len(head.data.shape_keys.key_blocks) == 52 and len(rig.animation_data.drivers) == 1957
bpy.ops.wm.save_as_mainfile(filepath=str((OUT / 'V772_feathered_beard_trial.blend').resolve()), compress=True)
(OUT / 'v772_beard_edge_trial.json').write_text(json.dumps({
    'beard_curves_before': len(counts), 'beard_curves_after': len(retained), 'fade_width_m': .007,
    'retained_beard_uvs_unchanged': True, 'other_four_grooms_unchanged': True,
    'face_shape_keys': 52, 'rig_drivers': 1957}, indent=2))
print('UNDERCOAT_AND_BEARD_TRIAL_COMPLETE', flush=True)
