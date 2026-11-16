"""Fill scalp coverage by surface area and tighten the licensed curl silhouette."""
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
assert head.get('v774_surface_area_beard')
assert bpy.data.objects.get('V775_SCALP_UNDERCOAT') is None
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


before = {name: fingerprint(name) for name in grooms[1:]}
scalp = bpy.data.objects[grooms[0]]
points, old_uvs, old_radii, old_counts = read_curves(scalp)
assert np.all(old_counts == 23)
paths = points.reshape(-1, 23, 3).astype(np.float64)
old_roots = paths[:, 0].copy()
old_tree = KDTree(len(old_roots))
for i, point in enumerate(old_roots):
    old_tree.insert(Vector(point), i)
old_tree.balance()
mesh = head.data
coords = np.empty((len(mesh.vertices), 3), np.float64)
mesh.shape_keys.key_blocks['Basis'].data.foreach_get('co', coords.ravel())
mesh.calc_loop_triangles()
triangles = np.array([t.vertices[:] for t in mesh.loop_triangles], np.int32)
tri_points = coords[triangles]
uv = np.array([[mesh.uv_layers['UVMap'].data[i].uv[:] for i in t.loops]
               for t in mesh.loop_triangles])
cross = np.cross(tri_points[:, 1]-tri_points[:, 0], tri_points[:, 2]-tri_points[:, 0])
area = np.linalg.norm(cross, axis=1)/2.
normals = np.zeros_like(coords)
for corner in range(3):
    np.add.at(normals, triangles[:, corner], cross)
normals /= np.maximum(np.linalg.norm(normals, axis=1, keepdims=True), 1e-12)
tree = BVHTree.FromPolygons(coords.tolist(), triangles.tolist(), all_triangles=True)
parts = json.loads((ROOT / 'v740_native_regions.json').read_text())['parts']
removed = set(parts['Eyes']['faces']) | set(parts['Mouth']['faces'])
kept = [i for i in range(len(mesh.polygons)+len(removed)) if i not in removed]
scalp_faces = set(parts['Scalp']['faces'])
candidates = np.array([i for i, t in enumerate(mesh.loop_triangles) if kept[t.polygon_index] in scalp_faces])
weights = area[candidates]/area[candidates].sum()
restore = runpy.run_path(str(ROOT / 'native_cranium_mapping.py'))['restore_upper_head']
rng = np.random.default_rng(775)
root_parts, normal_parts, uv_parts = [], [], []
accepted, target = 0, 45000
for batch in range(20):
    ids = rng.choice(candidates, 80000, p=weights)
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
    part_x = .041+.13*(y+.065)
    part_mask = (z > 1.690) & (y > -.09) & (y < .05)
    density = smooth((z-hairline)/.003)
    density *= np.where(part_mask, smooth((abs(x-part_x)-.0013)/.0015), 1.)
    take = np.flatnonzero(rng.random(len(ids)) < density)[:target-accepted]
    root_parts.append(roots[take]); normal_parts.append(normal[take])
    uv_parts.append(np.einsum('ni,nij->nj', bary[take], uv[ids[take]]))
    accepted += len(take)
    if accepted == target:
        break
assert accepted == target
roots, root_normals, root_uvs = map(np.concatenate, (root_parts, normal_parts, uv_parts))
# Reuse donor ringlet shapes in an independent, uniformly rooted short layer.
under_paths = []
for root, normal in zip(roots, root_normals):
    source = old_tree.find(Vector(root))[1]
    source_normal = tree.find_nearest(Vector(old_roots[source]))[1]
    rotation = np.array(source_normal.rotation_difference(Vector(normal)).to_matrix())
    delta = (paths[source]-old_roots[source]) @ rotation.T
    arc = np.linalg.norm(np.diff(delta, axis=0), axis=1).sum()
    delta *= rng.uniform(.006, .010)/max(arc, 1e-12)
    height = delta @ normal
    delta += np.maximum(.00008-height, 0.)[:, None]*normal
    under_paths.append(root+delta)
under_points = np.asarray(under_paths, np.float32).reshape(-1, 3)
assert np.isfinite(under_points).all()
data = bpy.data.hair_curves.new('V775_SURFACE_UNDERCOAT')
data.add_curves([23]*target)
data.set_types(type='CATMULL_ROM')
data.position_data.foreach_set('vector', under_points.ravel())
radii = np.tile(.000040*(1-.94*np.linspace(0, 1, 23)**2), target).astype(np.float32)
data.attributes.new('radius', 'FLOAT', 'POINT').data.foreach_set('value', radii)
data.attributes.new('surface_uv_coordinate', 'FLOAT2', 'CURVE').data.foreach_set('vector', root_uvs.astype(np.float32).ravel())
data.surface = head; data.surface_uv_map = 'UVMap'
data.surface_collision_distance = .00015
for material in scalp.data.materials:
    data.materials.append(material)
undercoat = scalp.copy()
undercoat.name = 'V775_SCALP_UNDERCOAT'; undercoat.data = data
for collection in scalp.users_collection:
    collection.objects.link(undercoat)
undercoat['adaptation'] = 'Bystedt curls sampled by native scalp surface area; short dense layer with feathered hairline'
# Reduce the swollen silhouette without changing roots, the part or curl topology.
crown = smooth((old_roots[:, 2]-1.680)/.060)
factors = .60+.18*crown
compact = old_roots[:, None]+(paths-old_roots[:, None])*factors[:, None, None]
scalp.data.position_data.foreach_set('vector', compact.astype(np.float32).ravel())
scalp['v775_curl_length_factor_sides_crown'] = [.60, .78]
assert all(fingerprint(name) == before[name] for name in grooms[1:])
assert np.array_equal(read_curves(scalp)[1], old_uvs)
assert np.array_equal(read_curves(scalp)[0].reshape(-1, 23, 3)[:, 0], old_roots.astype(np.float32))
head['v775_surface_scalp_undercoat'] = True
report = {'source': bpy.data.filepath, 'undercoat_curves': target,
          'undercoat_arc_length_target_m': [.006, .010], 'undercoat_radius_m': .000040,
          'foreground_length_factor_sides_crown': [.60, .78],
          'foreground_scalp_roots_uvs_unchanged': True, 'four_facial_grooms_unchanged': True,
          'face_shape_keys': len(mesh.shape_keys.key_blocks), 'rig_drivers': len(rig.animation_data.drivers),
          'license': 'licenses/hair-asset-sources.md'}
(OUT / 'v775_surface_scalp.json').write_text(json.dumps(report, indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str((OUT / 'V775_surface_scalp_trial.blend').resolve()), compress=True)
camera = json.loads((ROOT.parent / 'references/derived/photoreal_facebuilder_v1/fitted_camera_v761.json').read_text())
base = {'EXTRA_OBJECTS': grooms+[undercoat.name],
        'EXCLUDE_OBJECTS': ['V740_NATIVE_CURLS', 'V740_NATIVE_UNDERCOAT', 'V740_BROW_FIBERS', 'V740_BEARD_FIBERS'],
        'PRESERVE_MATERIALS': True, 'RESOLUTION': tuple(camera['size']),
        'SAMPLES': 128, 'ADAPTIVE_THRESHOLD': .02, 'DENOISE': True}
for tag, view, options in [
        ('v775_scalp', 'front', {}),
        ('v775_scalp', 'reference_orientation', {'CAMERA_RECORD': camera}),
        ('v775_motion', 'reference_orientation', {'CAMERA_RECORD': camera, 'HEAD_TURN_DEGREES': 12.,
                                                 'POSE': {'Blink.L': .65, 'Blink.R': .65}})]:
    runpy.run_path(str(ROOT / 'render_v740_cloud_groom.py'), init_globals={
        **base, **options, 'TAG': tag, 'VIEWS': [view]})
print('SURFACE_SCALP_TRIAL_COMPLETE', flush=True)
