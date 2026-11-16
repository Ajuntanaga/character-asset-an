"""Redistribute licensed beard strands by native face area, retaining UV animation."""
import hashlib
import json
import runpy
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

ROOT = Path(__file__).resolve().parent
OUT = Path('results')
OUT.mkdir(exist_ok=True)
head = bpy.data.objects['V740_NATIVE_FACE']
rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
assert head.get('v769_hair_shading_trial')
assert not head.get('v771_short_undercoat_trial')
assert len(head.data.shape_keys.key_blocks) == 52
assert len(rig.animation_data.drivers) == 1957
grooms = ['V766_ASSET_' + p for p in ('SCALP', 'BROWS', 'BEARD', 'MUSTACHE', 'LASHES')]


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


def smooth(value):
    value = np.clip(value, 0., 1.)
    return value * value * (3. - 2. * value)


def coverage(points, normals):
    x, y, z = points.T
    edge = np.interp(abs(x), [0., .025, .035, .050, .080, .095],
                     [1.562, 1.565, 1.585, 1.609, 1.640, 1.646])
    # Soft borders; no donor front projection or radial concentration at the jaw.
    density = (smooth((edge-z)/.006) * smooth((z-1.514)/.008)
               * smooth((-.010-y)/.015) * smooth((.091-abs(x))/.007)
               * smooth((.25-normals[:, 1])/.45))
    # The reference has a lighter upper cheek and a fuller chin, with visible skin.
    density *= .65 + .35 * smooth((1.570-z)/.025)
    return density


before = {name: fingerprint(name) for name in grooms}
mesh = head.data
coords = np.empty((len(mesh.vertices), 3), np.float64)
mesh.shape_keys.key_blocks['Basis'].data.foreach_get('co', coords.ravel())
mesh.calc_loop_triangles()
triangles = np.array([t.vertices[:] for t in mesh.loop_triangles], np.int32)
uv = np.array([[mesh.uv_layers['UVMap'].data[i].uv[:] for i in t.loops]
               for t in mesh.loop_triangles])
tri_points = coords[triangles]
cross = np.cross(tri_points[:, 1]-tri_points[:, 0], tri_points[:, 2]-tri_points[:, 0])
area = np.linalg.norm(cross, axis=1) / 2.
normals = np.zeros_like(coords)
for corner in range(3):
    np.add.at(normals, triangles[:, corner], cross)
normals /= np.maximum(np.linalg.norm(normals, axis=1, keepdims=True), 1e-12)
tree = BVHTree.FromPolygons(coords.tolist(), triangles.tolist(), all_triangles=True)
centers = tri_points.mean(axis=1)
candidates = np.flatnonzero((centers[:, 2] > 1.508) & (centers[:, 2] < 1.650)
                           & (centers[:, 1] < -.008) & (abs(centers[:, 0]) < .096))
weights = area[candidates] / area[candidates].sum()
rng = np.random.default_rng(774)
target = 24000
roots, root_normals, root_uvs, density_values = [], [], [], []
accepted = 0
for batch in range(20):
    ids = rng.choice(candidates, 50000, p=weights)
    a, b = rng.random((2, len(ids)))
    a = np.sqrt(a)
    bary = np.stack((1-a, a*(1-b), a*b), axis=1)
    points = np.einsum('ni,nij->nj', bary, tri_points[ids])
    normal = np.einsum('ni,nij->nj', bary, normals[triangles[ids]])
    normal /= np.maximum(np.linalg.norm(normal, axis=1, keepdims=True), 1e-12)
    density = coverage(points, normal)
    take = np.flatnonzero(rng.random(len(ids)) < density)[:target-accepted]
    roots.append(points[take])
    root_normals.append(normal[take])
    root_uvs.append(np.einsum('ni,nij->nj', bary[take], uv[ids[take]]))
    density_values.append(density[take])
    accepted += len(take)
    if accepted == target:
        break
assert accepted == target, accepted
roots, root_normals, root_uvs = map(np.concatenate, (roots, root_normals, root_uvs))
density_values = np.concatenate(density_values)

beard = bpy.data.objects['V766_ASSET_BEARD']
old_points, _, _, old_counts = read_curves(beard)
old_offsets = np.r_[0, np.cumsum(old_counts)]
old_roots = old_points[old_offsets[:-1]]
old_tree = KDTree(len(old_roots))
for index, point in enumerate(old_roots):
    old_tree.insert(Vector(point), index)
old_tree.balance()
old_normals = []
for point in old_roots:
    hit, face_normal, index, distance = tree.find_nearest(Vector(point))
    # Smooth normals prevent triangle edges from appearing in the groom.
    p0, p1, p2 = tri_points[index]
    edges = np.stack((p1-p0, p2-p0), axis=1)
    v, w = np.linalg.lstsq(edges, np.asarray(hit)-p0, rcond=None)[0]
    n = np.array((1-v-w, v, w)) @ normals[triangles[index]]
    old_normals.append(n / max(np.linalg.norm(n), 1e-12))

paths, radii = [], []
for index, (root, normal) in enumerate(zip(roots, root_normals)):
    nearby = old_tree.find_n(Vector(root), 8)
    source = nearby[int(rng.integers(len(nearby)))][1]
    path = old_points[old_offsets[source]:old_offsets[source+1]].astype(np.float64)
    delta = path-path[0]
    rotation = np.array(Vector(old_normals[source]).rotation_difference(Vector(normal)).to_matrix())
    delta = delta @ rotation.T
    length = np.linalg.norm(np.diff(delta, axis=0), axis=1).sum()
    assert length > 1e-8
    wanted = rng.uniform(.0025, .0045) * (.55 + .45 * np.sqrt(density_values[index]))
    delta *= wanted/length
    # Keep each strand outside the skin, including the jaw's curved surface.
    path = root + normal*.00008 + delta
    for j, point in enumerate(path):
        hit, n, _, distance = tree.find_nearest(Vector(point))
        signed = (Vector(point)-hit).dot(n)
        if signed < .00008:
            path[j] += np.asarray(n) * (.00008-signed)
    paths.append(path)
    radius = rng.uniform(.000032, .000043)
    radii.append(radius * (1-.94*np.linspace(0, 1, len(path))**2))

data = bpy.data.hair_curves.new('V774_SURFACE_AREA_BEARD')
counts = [len(path) for path in paths]
all_points = np.concatenate(paths).astype(np.float32)
assert np.isfinite(all_points).all() and np.isfinite(root_uvs).all()
data.add_curves(counts)
data.set_types(type='CATMULL_ROM')
data.position_data.foreach_set('vector', all_points.ravel())
data.attributes.new('radius', 'FLOAT', 'POINT').data.foreach_set('value', np.concatenate(radii).astype(np.float32))
data.attributes.new('surface_uv_coordinate', 'FLOAT2', 'CURVE').data.foreach_set('vector', root_uvs.astype(np.float32).ravel())
data.surface = head
data.surface_uv_map = 'UVMap'
data.surface_collision_distance = .00015
for material in beard.data.materials:
    data.materials.append(material)
old_data = beard.data
beard.data = data
if old_data.users == 0:
    bpy.data.hair_curves.remove(old_data)
beard['adaptation'] = 'Einar strand shapes redistributed by native face triangle area; feathered coverage and UV roots'
assert all(fingerprint(name) == before[name] for name in grooms if name != beard.name)
head['v774_surface_area_beard'] = True
bpy.context.view_layer.update()
np.savez_compressed(OUT / 'v774_beard_roots.npz', old=old_roots, new=roots, uvs=root_uvs)
report = {'source': bpy.data.filepath, 'beard_curves_before': len(old_counts),
          'beard_curves_after': len(counts), 'other_four_grooms_unchanged': True,
          'sampled_face_area_m2': float(area[candidates].sum()),
          'root_bounds': [roots.min(axis=0).tolist(), roots.max(axis=0).tolist()],
          'strand_length_target_m': [.0025, .0045], 'root_radius_m': [.000032, .000043],
          'surface': data.surface.name, 'surface_uv_map': data.surface_uv_map,
          'face_shape_keys': len(mesh.shape_keys.key_blocks),
          'rig_drivers': len(rig.animation_data.drivers),
          'license': 'licenses/hair-asset-sources.md'}
(OUT / 'v774_surface_beard.json').write_text(json.dumps(report, indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str((OUT / 'V774_surface_beard_trial.blend').resolve()), compress=True)

camera = json.loads((ROOT.parent / 'references/derived/photoreal_facebuilder_v1/fitted_camera_v761.json').read_text())
base = {'EXTRA_OBJECTS': grooms,
        'EXCLUDE_OBJECTS': ['V740_NATIVE_CURLS', 'V740_NATIVE_UNDERCOAT', 'V740_BROW_FIBERS', 'V740_BEARD_FIBERS'],
        'PRESERVE_MATERIALS': True, 'RESOLUTION': tuple(camera['size']),
        'SAMPLES': 128, 'ADAPTIVE_THRESHOLD': .02, 'DENOISE': True}
for tag, view, options in [
        ('v774_beard', 'front', {}),
        ('v774_beard', 'reference_orientation', {'CAMERA_RECORD': camera}),
        ('v774_motion', 'reference_orientation', {'CAMERA_RECORD': camera, 'HEAD_TURN_DEGREES': 12.,
                                                  'POSE': {'Blink.L': .65, 'Blink.R': .65}})]:
    runpy.run_path(str(ROOT / 'render_v740_cloud_groom.py'), init_globals={
        **base, **options, 'TAG': tag, 'VIEWS': [view]})
print('SURFACE_BEARD_TRIAL_COMPLETE', flush=True)
