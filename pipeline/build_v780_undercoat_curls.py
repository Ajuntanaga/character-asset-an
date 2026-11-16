"""Replace repeated undercoat shapes with independent licensed donor curls."""
import hashlib
import json
import runpy
from pathlib import Path

import bpy
import numpy as np
from mathutils import Quaternion, Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parent
OUT = Path('results')
OUT.mkdir(exist_ok=True)
head = bpy.data.objects['V740_NATIVE_FACE']
rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
assert head.get('v779_temple_coverage')
assert len(head.data.shape_keys.key_blocks) == 52
assert len(rig.animation_data.drivers) == 1957
grooms = ['V766_ASSET_' + p for p in ('SCALP', 'BROWS', 'BEARD', 'MUSTACHE', 'LASHES')]
grooms += ['V779_TEMPLE_HAIR']


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


before = {name: fingerprint(name) for name in grooms}
undercoat = bpy.data.objects['V775_SCALP_UNDERCOAT']
old_points, old_uvs, old_radii, old_counts = read_curves(undercoat)
assert len(old_counts) == 45000 and np.all(old_counts == 23)
roots = old_points.reshape(-1, 23, 3)[:, 0].copy()
assert undercoat.data.surface == head
assert undercoat.data.surface_uv_map == 'UVMap'
modifier_group = undercoat.modifiers['Follow native face and FACS'].node_group
materials = list(undercoat.data.materials)
matrix = undercoat.matrix_world.copy()

donor = np.load(ROOT.parent/'assets/licensed-hair-library/bystedt_curls.npz')
assert np.all(np.diff(donor['offsets']) == 23)
donor_paths = donor['points'].reshape(-1, 23, 3).astype(np.float64)
donor_delta = donor_paths-donor_paths[:, :1]
donor_arcs = np.linalg.norm(np.diff(donor_delta, axis=1), axis=2).sum(axis=1)
assert np.all(donor_arcs > 0.)

# Interpolate smooth normals at the original roots; do not resample the roots.
mesh = head.data
co = np.empty((len(mesh.vertices), 3), np.float64)
mesh.shape_keys.key_blocks['Basis'].data.foreach_get('co', co.ravel())
mesh.calc_loop_triangles()
triangles = np.array([t.vertices[:] for t in mesh.loop_triangles], np.int32)
tri_points = co[triangles]
cross = np.cross(tri_points[:, 1]-tri_points[:, 0], tri_points[:, 2]-tri_points[:, 0])
normals = np.zeros_like(co)
for corner in range(3):
    np.add.at(normals, triangles[:, corner], cross)
normals /= np.maximum(np.linalg.norm(normals, axis=1, keepdims=True), 1e-12)
tree = BVHTree.FromPolygons(co.tolist(), triangles.tolist(), all_triangles=True)
rng = np.random.default_rng(780)
new_paths, source_ids, root_distances = [], [], []
for root in roots:
    hit, _, index, distance = tree.find_nearest(Vector(root))
    assert index is not None
    a, b, c = tri_points[index]
    v0, v1, v2 = b-a, c-a, np.asarray(hit)-a
    d00, d01, d11 = v0@v0, v0@v1, v1@v1
    denominator = d00*d11-d01*d01
    assert denominator > 1e-24
    v = (d11*(v2@v0)-d01*(v2@v1))/denominator
    w = (d00*(v2@v1)-d01*(v2@v0))/denominator
    bary = np.array((1-v-w, v, w))
    normal = bary @ normals[triangles[index]]
    normal /= np.linalg.norm(normal)
    source = int(rng.integers(len(donor_delta)))
    down = np.array((0., .20, -1.))
    down -= normal*(down@normal)
    down /= max(np.linalg.norm(down), 1e-12)
    direction = normal+.50*down
    direction /= np.linalg.norm(direction)
    align = Vector(donor_delta[source, -1]).rotation_difference(Vector(direction))
    roll = Quaternion(Vector(direction), float(rng.uniform(-np.pi, np.pi)))
    delta = donor_delta[source] @ np.array((roll@align).to_matrix()).T
    delta *= rng.uniform(.006, .010)/donor_arcs[source]
    # Roots already have the V775 surface clearance. Preserve their exact bytes.
    delta += np.maximum(-delta@normal, 0.)[:, None]*normal
    new_paths.append(root+delta)
    source_ids.append(source)
    root_distances.append(distance)

new_points = np.asarray(new_paths, np.float32).reshape(-1, 3)
assert np.isfinite(new_points).all()
assert np.array_equal(new_points.reshape(-1, 23, 3)[:, 0], roots)
undercoat.data.position_data.foreach_set('vector', new_points.ravel())
undercoat['adaptation'] = 'Independent original Bystedt curls with random axial roll; V775 roots, radii, UV attachment and material retained'
after = read_curves(undercoat)
assert all(np.array_equal(a, b) for a, b in zip(after[1:], (old_uvs, old_radii, old_counts)))
assert all(fingerprint(name) == before[name] for name in grooms)
assert undercoat.modifiers['Follow native face and FACS'].node_group == modifier_group
assert list(undercoat.data.materials) == materials and undercoat.matrix_world == matrix
assert np.max(root_distances) < .0003
head['v780_independent_undercoat'] = True
report = {'source': bpy.data.filepath, 'undercoat_curves': len(roots),
          'distinct_original_donors': len(set(source_ids)),
          'arc_length_nominal_range_m': [.006, .010], 'random_roll_degrees': [-180, 180],
          'max_root_surface_distance_m': float(np.max(root_distances)),
          'roots_uvs_radii_topology_unchanged': True, 'six_other_grooms_unchanged': True,
          'materials_and_deformation_modifier_unchanged': True,
          'face_shape_keys': len(mesh.shape_keys.key_blocks), 'rig_drivers': len(rig.animation_data.drivers),
          'license': 'licenses/hair-asset-sources.md'}
(OUT/'v780_undercoat_curls.json').write_text(json.dumps(report, indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str((OUT/'V780_undercoat_curls_trial.blend').resolve()), compress=True)
camera = json.loads((ROOT.parent/'references/derived/photoreal_facebuilder_v1/fitted_camera_v761.json').read_text())
base = {'EXTRA_OBJECTS': grooms+[undercoat.name],
        'EXCLUDE_OBJECTS': ['V740_NATIVE_CURLS', 'V740_NATIVE_UNDERCOAT', 'V740_BROW_FIBERS', 'V740_BEARD_FIBERS'],
        'PRESERVE_MATERIALS': True, 'RESOLUTION': tuple(camera['size']),
        'SAMPLES': 128, 'ADAPTIVE_THRESHOLD': .02, 'DENOISE': True}
for tag, view, options in [
        ('v780_undercoat', 'front', {}),
        ('v780_undercoat', 'reference_orientation', {'CAMERA_RECORD': camera}),
        ('v780_motion', 'reference_orientation', {'CAMERA_RECORD': camera, 'HEAD_TURN_DEGREES': 12.,
                                                 'POSE': {'Blink.L': .65, 'Blink.R': .65}})]:
    runpy.run_path(str(ROOT/'render_v740_cloud_groom.py'), init_globals={
        **base, **options, 'TAG': tag, 'VIEWS': [view]})
print('INDEPENDENT_UNDERCOAT_TRIAL_COMPLETE', flush=True)
