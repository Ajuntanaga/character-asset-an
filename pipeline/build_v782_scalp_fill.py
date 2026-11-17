"""Increase short-curl coverage after the V781 layer isolation render."""
import hashlib
import json
from pathlib import Path
import runpy

import bpy
import numpy as np
from mathutils import Quaternion, Vector

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(globals().get('OUT', ROOT / 'results'))
OUT.mkdir(parents=True, exist_ok=True)
RENDER = globals().get('RENDER', True)
head = bpy.data.objects['V740_NATIVE_FACE']
rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
assert head.get('v779_temple_coverage') and not head.get('v782_scalp_fill')
assert len(head.data.shape_keys.key_blocks) == 52
assert len(rig.animation_data.drivers) == 1957
grooms = ['V766_ASSET_' + part for part in ('SCALP', 'BROWS', 'BEARD', 'MUSTACHE', 'LASHES')]
grooms += ['V779_TEMPLE_HAIR']


def fingerprint(name):
    data = bpy.data.objects[name].data
    points = np.empty(len(data.position_data) * 3, np.float32)
    data.position_data.foreach_get('vector', points)
    uvs = np.empty(len(data.curves) * 2, np.float32)
    data.attributes['surface_uv_coordinate'].data.foreach_get('vector', uvs)
    radii = np.empty(len(data.position_data), np.float32)
    data.attributes['radius'].data.foreach_get('value', radii)
    counts = np.array([len(curve.points) for curve in data.curves], np.int32)
    return hashlib.sha256(b''.join(a.tobytes() for a in (points, uvs, radii, counts))).hexdigest()


def smooth(value):
    value = np.clip(value, 0., 1.)
    return value * value * (3. - 2. * value)


before = {name: fingerprint(name) for name in grooms}
undercoat = bpy.data.objects['V775_SCALP_UNDERCOAT']
old_data = undercoat.data
assert len(old_data.curves) == 45000
modifier_group = undercoat.modifiers['Follow native face and FACS'].node_group
old_materials = list(old_data.materials)
old_matrix = undercoat.matrix_world.copy()

# Use the accepted V775 scalp area and feathered hairline/part masks.
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
parts = json.loads((ROOT / 'pipeline/v740_native_regions.json').read_text())['parts']
removed = set(parts['Eyes']['faces']) | set(parts['Mouth']['faces'])
kept = [i for i in range(len(mesh.polygons)+len(removed)) if i not in removed]
scalp_faces = set(parts['Scalp']['faces'])
candidates = np.array([i for i, t in enumerate(mesh.loop_triangles)
                       if kept[t.polygon_index] in scalp_faces])
weights = area[candidates]/area[candidates].sum()
restore = runpy.run_path(str(ROOT / 'pipeline/native_cranium_mapping.py'))['restore_upper_head']
rng = np.random.default_rng(782)
root_parts, normal_parts, uv_parts = [], [], []
accepted, target = 0, 180000
for batch in range(30):
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
    root_parts.append(roots[take])
    normal_parts.append(normal[take])
    uv_parts.append(np.einsum('ni,nij->nj', bary[take], uv[ids[take]]))
    accepted += len(take)
    if accepted == target:
        break
assert accepted == target
roots, root_normals, root_uvs = map(np.concatenate, (root_parts, normal_parts, uv_parts))

# Original independent donor curls retain their licensed shapes; the shorter
# V780 experiment established that shape variation alone did not fill the scalp.
donor = np.load(ROOT / 'assets/licensed-hair-library/bystedt_curls.npz')
assert np.all(np.diff(donor['offsets']) == 23)
donor_paths = donor['points'].reshape(-1, 23, 3).astype(np.float64)
donor_delta = donor_paths-donor_paths[:, :1]
donor_arcs = np.linalg.norm(np.diff(donor_delta, axis=1), axis=2).sum(axis=1)
assert np.all(donor_arcs > 0.)
source_ids = rng.integers(len(donor_delta), size=target)
nominal_arcs = rng.uniform(.012, .018, size=target)
rolls = rng.uniform(-np.pi, np.pi, size=target)
paths = np.empty((target, 23, 3), np.float32)
for i, (root, normal, source, arc, angle) in enumerate(zip(
        roots, root_normals, source_ids, nominal_arcs, rolls)):
    down = np.array((0., .20, -1.))
    down -= normal*(down@normal)
    down /= max(np.linalg.norm(down), 1e-12)
    direction = normal+.50*down
    direction /= np.linalg.norm(direction)
    align = Vector(donor_delta[source, -1]).rotation_difference(Vector(direction))
    roll = Quaternion(Vector(direction), float(angle))
    delta = donor_delta[source] @ np.array((roll@align).to_matrix()).T
    delta *= arc/donor_arcs[source]
    delta += np.maximum(.00008-delta@normal, 0.)[:, None]*normal
    paths[i] = root+delta
assert np.isfinite(paths).all()
data = bpy.data.hair_curves.new('V782_DENSE_SHORT_CURLS')
data.add_curves([23]*target)
data.set_types(type='CATMULL_ROM')
data.position_data.foreach_set('vector', paths.ravel())
radii = np.tile(.000040*(1-.94*np.linspace(0, 1, 23)**2), target).astype(np.float32)
data.attributes.new('radius', 'FLOAT', 'POINT').data.foreach_set('value', radii)
data.attributes.new('surface_uv_coordinate', 'FLOAT2', 'CURVE').data.foreach_set(
    'vector', root_uvs.astype(np.float32).ravel())
data.surface = head
data.surface_uv_map = 'UVMap'
data.surface_collision_distance = .00015
for material in old_materials:
    data.materials.append(material)
undercoat.data = data
undercoat['adaptation'] = 'Independent Bystedt short curls; denser surface-area coverage with original hairline and part masks'
assert all(fingerprint(name) == before[name] for name in grooms)
assert undercoat.modifiers['Follow native face and FACS'].node_group == modifier_group
assert list(data.materials) == old_materials and undercoat.matrix_world == old_matrix
assert len(mesh.shape_keys.key_blocks) == 52 and len(rig.animation_data.drivers) == 1957
head['v782_scalp_fill'] = True
report = {'source': bpy.data.filepath, 'undercoat_curves_before': 45000,
          'undercoat_curves_after': target, 'nominal_arc_length_m': [.012, .018],
          'radius_m': .000040, 'distinct_donors': int(len(np.unique(source_ids))),
          'scalp_surface_area_m2_before_hairline_mask': float(area[candidates].sum()),
          'hairline_part_density_function_unchanged': True,
          'six_other_grooms_unchanged': True, 'materials_and_attachment_unchanged': True,
          'face_shape_keys': 52, 'rig_drivers': 1957,
          'license': 'licenses/hair-asset-sources.md'}
(OUT / 'v782_scalp_fill.json').write_text(json.dumps(report, indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str((OUT / 'V782_scalp_fill_trial.blend').resolve()), compress=True)

if RENDER:
    camera = json.loads((ROOT / 'references/derived/photoreal_facebuilder_v1/fitted_camera_v761.json').read_text())
    base = {'EXTRA_OBJECTS': grooms+[undercoat.name],
            'EXCLUDE_OBJECTS': ['V740_NATIVE_CURLS', 'V740_NATIVE_UNDERCOAT', 'V740_BROW_FIBERS', 'V740_BEARD_FIBERS'],
            'PRESERVE_MATERIALS': True, 'RESOLUTION': tuple(camera['size']),
            'SAMPLES': 128, 'ADAPTIVE_THRESHOLD': .02, 'DENOISE': True}
    for tag, options in [
            ('v782_fill', {}),
            ('v782_short', {'EXCLUDE_OBJECTS': base['EXCLUDE_OBJECTS']+['V766_ASSET_SCALP'],
                            'BORDER': (.10, .85, .57, .98)}),
            ('v782_motion', {'HEAD_TURN_DEGREES': 12., 'POSE': {'Blink.L': .65, 'Blink.R': .65}})]:
        runpy.run_path(str(ROOT / 'pipeline/render_v740_cloud_groom.py'), init_globals={
            **base, **options, 'CAMERA_RECORD': camera, 'TAG': tag, 'VIEWS': ['reference_orientation']})
        rendered = json.loads((ROOT / 'results' / (tag+'_render_report.json')).read_text())
        assert rendered['production_unchanged'] and rendered['head_basis_restored']
        assert rendered['rig_drivers'] == 1957
    print('SCALP_FILL_TRIAL_COMPLETE', flush=True)
