"""Fit independent licensed short curls onto the missing temple surface."""
import hashlib
import json
import runpy
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector, Quaternion

ROOT = Path(__file__).resolve().parent
OUT = Path('results')
OUT.mkdir(exist_ok=True)
head = bpy.data.objects['V740_NATIVE_FACE']
rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
assert head.get('v776_mustache_density')
assert bpy.data.objects.get('V779_TEMPLE_HAIR') is None
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
donor = np.load(ROOT.parent/'assets/licensed-hair-library/bystedt_curls.npz')
assert np.all(np.diff(donor['offsets']) == 23)
donor_paths = donor['points'].reshape(-1, 23, 3).astype(np.float64)
donor_delta = donor_paths-donor_paths[:, :1]
donor_arcs = np.linalg.norm(np.diff(donor_delta, axis=1), axis=2).sum(axis=1)
assert np.all(donor_arcs > 0.)
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
rng = np.random.default_rng(778)  # Preserve V778 root samples; replace strand shapes only.
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
    source = int(rng.integers(len(donor_delta)))
    down = np.array((0., .20, -1.))
    down -= normal*(down@normal)
    down /= max(np.linalg.norm(down), 1e-12)
    direction = normal+.50*down
    direction /= np.linalg.norm(direction)
    align = Vector(donor_delta[source, -1]).rotation_difference(Vector(direction))
    roll = Quaternion(Vector(direction), float(rng.uniform(-np.pi, np.pi)))
    rotation = np.array((roll@align).to_matrix())
    delta = donor_delta[source] @ rotation.T
    length = (.004+.005*float(smooth((root[2]-1.655)/.045)))*rng.uniform(.80, 1.20)
    delta *= length/donor_arcs[source]
    delta += np.maximum(.00006-delta@normal, 0.)[:, None]*normal
    new_paths.append(root+delta)
new_points = np.asarray(new_paths, np.float32).reshape(-1, 3)
assert np.isfinite(new_points).all()
data = bpy.data.hair_curves.new('V779_TEMPLE_CURLS')
data.add_curves([23]*target)
data.set_types(type='CATMULL_ROM')
data.position_data.foreach_set('vector', new_points.ravel())
radii = np.tile(.000028*(1-.94*np.linspace(0, 1, 23)**2), target).astype(np.float32)
data.attributes.new('radius', 'FLOAT', 'POINT').data.foreach_set('value', radii)
data.attributes.new('surface_uv_coordinate', 'FLOAT2', 'CURVE').data.foreach_set('vector', root_uvs.astype(np.float32).ravel())
data.surface = head
data.surface_uv_map = 'UVMap'
data.surface_collision_distance = .00015
for material in scalp.data.materials:
    data.materials.append(material)
obj = scalp.copy()
obj.name = 'V779_TEMPLE_HAIR'
obj.data = data
for collection in scalp.users_collection:
    collection.objects.link(obj)
obj['adaptation'] = 'Independent original Bystedt curls, random roll, short tapered temple coverage; ears excluded'
assert obj.modifiers['Follow native face and FACS'].node_group == scalp.modifiers['Follow native face and FACS'].node_group
assert all(fingerprint(name) == before[name] for name in grooms)
head['v779_temple_coverage'] = True
report = {'source': bpy.data.filepath, 'temple_curves': target,
          'root_bounds': [roots.min(axis=0).tolist(), roots.max(axis=0).tolist()],
          'root_radius_m': .000028, 'arc_length_nominal_range_m': [.004, .009],
          'left_right_root_counts': [int((roots[:, 0] < 0).sum()), int((roots[:, 0] > 0).sum())],
          'ears_and_central_forehead_excluded': True,
          'six_existing_grooms_unchanged': True, 'surface_uv_attachment': True,
          'scalp_material_and_node_group_inherited': True,
          'direct_original_donor_paths': True, 'random_roll_degrees': [-180, 180],
          'face_shape_keys': len(mesh.shape_keys.key_blocks), 'rig_drivers': len(rig.animation_data.drivers),
          'license': 'licenses/hair-asset-sources.md'}
(OUT/'v779_temple_coverage.json').write_text(json.dumps(report, indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str((OUT/'V779_temple_coverage_trial.blend').resolve()), compress=True)
camera = json.loads((ROOT.parent/'references/derived/photoreal_facebuilder_v1/fitted_camera_v761.json').read_text())
base = {'EXTRA_OBJECTS': grooms+[obj.name],
        'EXCLUDE_OBJECTS': ['V740_NATIVE_CURLS', 'V740_NATIVE_UNDERCOAT', 'V740_BROW_FIBERS', 'V740_BEARD_FIBERS'],
        'PRESERVE_MATERIALS': True, 'RESOLUTION': tuple(camera['size']),
        'SAMPLES': 128, 'ADAPTIVE_THRESHOLD': .02, 'DENOISE': True}
for tag, view, options in [
        ('v779_temple', 'front', {}),
        ('v779_temple', 'reference_orientation', {'CAMERA_RECORD': camera}),
        ('v779_motion', 'reference_orientation', {'CAMERA_RECORD': camera, 'HEAD_TURN_DEGREES': 12.,
                                                 'POSE': {'Blink.L': .65, 'Blink.R': .65}})]:
    runpy.run_path(str(ROOT/'render_v740_cloud_groom.py'), init_globals={
        **base, **options, 'TAG': tag, 'VIEWS': [view]})
print('TEMPLE_COVERAGE_TRIAL_COMPLETE', flush=True)
