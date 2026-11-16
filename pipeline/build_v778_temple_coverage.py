"""Extend licensed curls onto the temple surface omitted by the scalp region."""
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
assert head.get('v776_mustache_density')
assert bpy.data.objects.get('V778_TEMPLE_HAIR') is None
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
    counts = np.array([len(c.points) for c in data.curves], np.int32)
    return points, uvs, radii, counts


def fingerprint(name):
    return hashlib.sha256(b''.join(a.tobytes() for a in read_curves(bpy.data.objects[name]))).hexdigest()


def smooth(t):
    t = np.clip(t, 0., 1.)
    return t*t*(3.-2.*t)


before = {name: fingerprint(name) for name in grooms}
scalp = bpy.data.objects['V766_ASSET_SCALP']
points, _, _, counts = read_curves(scalp)
assert np.all(counts == 23)
paths = points.reshape(-1, 23, 3).astype(np.float64)
source_roots = paths[:, 0].copy()
source_tree = KDTree(len(source_roots))
for i, point in enumerate(source_roots):
    source_tree.insert(Vector(point), i)
source_tree.balance()
mesh = head.data
co = np.empty((len(mesh.vertices), 3), np.float64)
mesh.shape_keys.key_blocks['Basis'].data.foreach_get('co', co.ravel())
mesh.calc_loop_triangles()
triangles = np.array([t.vertices[:] for t in mesh.loop_triangles], np.int32)
tri_points = co[triangles]
uv = np.array([[mesh.uv_layers['UVMap'].data[i].uv[:] for i in t.loops]
               for t in mesh.loop_triangles])
cross = np.cross(tri_points[:, 1]-tri_points[:, 0], tri_points[:, 2]-tri_points[:, 0])
areas = np.linalg.norm(cross, axis=1)/2.
normals = np.zeros_like(co)
for corner in range(3):
    np.add.at(normals, triangles[:, corner], cross)
normals /= np.maximum(np.linalg.norm(normals, axis=1, keepdims=True), 1e-12)
tree = BVHTree.FromPolygons(co.tolist(), triangles.tolist(), all_triangles=True)
parts = json.loads((ROOT/'v740_native_regions.json').read_text())['parts']
removed = set(parts['Eyes']['faces']) | set(parts['Mouth']['faces'])
kept = [i for i in range(len(mesh.polygons)+len(removed)) if i not in removed]
scalp_faces = set(parts['Scalp']['faces'])
centers = tri_points.mean(axis=1)
# Coarse triangle bounds only accelerate sampling. The continuous root mask below
# excludes the ears, central forehead, and lower sideburn, with feathered edges.
candidates = np.array([i for i, t in enumerate(mesh.loop_triangles)
                       if kept[t.polygon_index] not in scalp_faces
                       and centers[i, 2] > 1.649 and abs(centers[i, 0]) > .050
                       and centers[i, 1] < .005], np.int32)
weights = areas[candidates]/areas[candidates].sum()
restore = runpy.run_path(str(ROOT/'native_cranium_mapping.py'))['restore_upper_head']
rng = np.random.default_rng(778)
root_parts, normal_parts, uv_parts = [], [], []
accepted, target = 0, 8000
for batch in range(20):
    ids = rng.choice(candidates, 30000, p=weights)
    a, b = rng.random((2, len(ids)))
    a = np.sqrt(a)
    bary = np.stack((1-a, a*(1-b), a*b), axis=1)
    roots = np.einsum('ni,nij->nj', bary, tri_points[ids])
    normal = np.einsum('ni,nij->nj', bary, normals[triangles[ids]])
    normal /= np.maximum(np.linalg.norm(normal, axis=1, keepdims=True), 1e-12)
    x, y, z = roots.T
    front = 1.703-.060*smooth((abs(x)-.052)/.041)
    transition = smooth((y+.050)/.080)
    hairline = restore(front*(1-transition)+1.595*transition)
    density = smooth((z-hairline)/.003)
    density *= smooth((z-1.655)/.003)*smooth((abs(x)-.058)/.005)
    density *= smooth((.099-abs(x))/.004)*smooth((-.005-y)/.005)
    take = np.flatnonzero(rng.random(len(ids)) < density)[:target-accepted]
    root_parts.append(roots[take]); normal_parts.append(normal[take])
    uv_parts.append(np.einsum('ni,nij->nj', bary[take], uv[ids[take]]))
    accepted += len(take)
    if accepted == target:
        break
assert accepted == target
roots, root_normals, root_uvs = map(np.concatenate, (root_parts, normal_parts, uv_parts))
assert np.all(roots[:, 2] > 1.655) and np.all(roots[:, 1] < -.005)
assert np.all((abs(roots[:, 0]) > .058) & (abs(roots[:, 0]) < .099))
new_paths = []
for root, normal in zip(roots, root_normals):
    source = source_tree.find(Vector(root))[1]
    source_normal = tree.find_nearest(Vector(source_roots[source]))[1]
    rotation = np.array(source_normal.rotation_difference(Vector(normal)).to_matrix())
    delta = (paths[source]-source_roots[source]) @ rotation.T
    arc = np.linalg.norm(np.diff(delta, axis=0), axis=1).sum()
    length = (.006+.008*float(smooth((root[2]-1.655)/.045)))*rng.uniform(.85, 1.15)
    delta *= length/max(arc, 1e-12)
    delta += np.maximum(.00008-delta@normal, 0.)[:, None]*normal
    new_paths.append(root+delta)
new_points = np.asarray(new_paths, np.float32).reshape(-1, 3)
assert np.isfinite(new_points).all()
data = bpy.data.hair_curves.new('V778_TEMPLE_CURLS')
data.add_curves([23]*target)
data.set_types(type='CATMULL_ROM')
data.position_data.foreach_set('vector', new_points.ravel())
radii = np.tile(.000038*(1-.94*np.linspace(0, 1, 23)**2), target).astype(np.float32)
data.attributes.new('radius', 'FLOAT', 'POINT').data.foreach_set('value', radii)
data.attributes.new('surface_uv_coordinate', 'FLOAT2', 'CURVE').data.foreach_set('vector', root_uvs.astype(np.float32).ravel())
data.surface = head
data.surface_uv_map = 'UVMap'
data.surface_collision_distance = .00015
for material in scalp.data.materials:
    data.materials.append(material)
obj = scalp.copy()
obj.name = 'V778_TEMPLE_HAIR'
obj.data = data
for collection in scalp.users_collection:
    collection.objects.link(obj)
obj['adaptation'] = 'Licensed Bystedt curl shapes on feathered native temple surface; ears excluded'
assert obj.modifiers['Follow native face and FACS'].node_group == scalp.modifiers['Follow native face and FACS'].node_group
assert all(fingerprint(name) == before[name] for name in grooms)
head['v778_temple_coverage'] = True
report = {'source': bpy.data.filepath, 'temple_curves': target,
          'root_bounds': [roots.min(axis=0).tolist(), roots.max(axis=0).tolist()],
          'root_radius_m': .000038, 'arc_length_nominal_range_m': [.006, .014],
          'left_right_root_counts': [int((roots[:, 0] < 0).sum()), int((roots[:, 0] > 0).sum())],
          'ears_and_central_forehead_excluded': True,
          'six_existing_grooms_unchanged': True, 'surface_uv_attachment': True,
          'scalp_material_and_node_group_inherited': True,
          'face_shape_keys': len(mesh.shape_keys.key_blocks), 'rig_drivers': len(rig.animation_data.drivers),
          'license': 'licenses/hair-asset-sources.md'}
(OUT/'v778_temple_coverage.json').write_text(json.dumps(report, indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str((OUT/'V778_temple_coverage_trial.blend').resolve()), compress=True)
camera = json.loads((ROOT.parent/'references/derived/photoreal_facebuilder_v1/fitted_camera_v761.json').read_text())
base = {'EXTRA_OBJECTS': grooms+[obj.name],
        'EXCLUDE_OBJECTS': ['V740_NATIVE_CURLS', 'V740_NATIVE_UNDERCOAT', 'V740_BROW_FIBERS', 'V740_BEARD_FIBERS'],
        'PRESERVE_MATERIALS': True, 'RESOLUTION': tuple(camera['size']),
        'SAMPLES': 128, 'ADAPTIVE_THRESHOLD': .02, 'DENOISE': True}
for tag, view, options in [
        ('v778_temple', 'front', {}),
        ('v778_temple', 'reference_orientation', {'CAMERA_RECORD': camera}),
        ('v778_motion', 'reference_orientation', {'CAMERA_RECORD': camera, 'HEAD_TURN_DEGREES': 12.,
                                                 'POSE': {'Blink.L': .65, 'Blink.R': .65}})]:
    runpy.run_path(str(ROOT/'render_v740_cloud_groom.py'), init_globals={
        **base, **options, 'TAG': tag, 'VIEWS': [view]})
print('TEMPLE_COVERAGE_TRIAL_COMPLETE', flush=True)
