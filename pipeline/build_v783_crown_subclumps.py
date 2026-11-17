"""Split synchronized outer crown bundles using licensed donor curl shapes."""
import hashlib
import json
from pathlib import Path
import runpy

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(globals().get('OUT', ROOT / 'results'))
OUT.mkdir(parents=True, exist_ok=True)
APPLY = globals().get('APPLY', True)
RENDER = globals().get('RENDER', True)
head = bpy.data.objects['V740_NATIVE_FACE']
rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
assert head.get('v782_scalp_fill') and not head.get('v783_crown_subclumps')
assert len(head.data.shape_keys.key_blocks) == 52
assert len(rig.animation_data.drivers) == 1957
obj = bpy.data.objects['V766_ASSET_SCALP']
data = obj.data
assert len(data.curves) == 66765 and len(data.position_data) == 66765 * 23


def values(attribute, field, width=1):
    out = np.empty((len(attribute.data), width), np.float32)
    attribute.data.foreach_get(field, out.ravel())
    return out


def fingerprint(name):
    curves = bpy.data.objects[name].data
    points = np.empty(len(curves.position_data) * 3, np.float32)
    curves.position_data.foreach_get('vector', points)
    return hashlib.sha256(points.tobytes()).hexdigest()


def unit(vector):
    return vector / max(float(np.linalg.norm(vector)), 1e-12)


def smooth(value):
    value = np.clip(value, 0., 1.)
    return value * value * (3. - 2. * value)


def frame(delta):
    axis = unit(delta[-1])
    transverse = delta - (delta @ axis)[:, None] * axis
    bend = unit(transverse[np.argmax(np.linalg.norm(transverse, axis=1))])
    assert np.linalg.norm(bend) > .99
    return np.stack((bend, np.cross(axis, bend), axis), axis=1)


old = np.empty((len(data.curves), 23, 3), np.float32)
data.position_data.foreach_get('vector', old.ravel())
roots = old[:, 0].astype(np.float64)
uvs = values(data.attributes['surface_uv_coordinate'], 'vector', 2)
radii = values(data.attributes['radius'], 'value')
other_grooms = ['V766_ASSET_' + p for p in ('BROWS', 'BEARD', 'MUSTACHE', 'LASHES')]
other_grooms += ['V775_SCALP_UNDERCOAT', 'V779_TEMPLE_HAIR']
before = {name: fingerprint(name) for name in other_grooms}
materials = list(data.materials)
attachment = obj.modifiers['Follow native face and FACS'].node_group

# V766 installed three closely spaced siblings for each original donor root.
# Cluster the parent centers, so siblings retain the same curl phase.
parent_roots = roots.reshape(-1, 3, 3).mean(axis=1)
assert np.max(np.linalg.norm(roots.reshape(-1, 3, 3)-parent_roots[:, None], axis=2)) < .0004
part_sides = parent_roots[:, 0] >= .041 + .13 * (parent_roots[:, 1] + .065)
assignment = np.full(len(parent_roots), -1, np.int32)
guides = []
for side in (False, True):
    ids = np.flatnonzero(part_sides == side)
    positions = parent_roots[ids]
    nearest = np.full(len(ids), np.inf)
    chosen = int(np.argmax(positions[:, 2]))
    while True:
        guide = int(ids[chosen])
        distance = np.sum((positions-positions[chosen])**2, axis=1)
        closer = distance < nearest
        nearest[closer] = distance[closer]
        assignment[ids[closer]] = guide
        guides.append(guide)
        chosen = int(np.argmax(nearest))
        if nearest[chosen] <= .0065**2:
            break
assert np.all(assignment >= 0) and np.all(part_sides == part_sides[assignment])

mesh = head.data
coords = np.empty((len(mesh.vertices), 3), np.float64)
mesh.shape_keys.key_blocks['Basis'].data.foreach_get('co', coords.ravel())
mesh.calc_loop_triangles()
tree = BVHTree.FromPolygons(coords.tolist(), [t.vertices[:] for t in mesh.loop_triangles], all_triangles=True)
with np.load(ROOT / 'assets/licensed-hair-library/bystedt_curls.npz') as source:
    assert np.all(np.diff(source['offsets']) == 23)
    donor = source['points'].reshape(-1, 23, 3).astype(np.float64)
donor -= donor[:, :1].copy()
donor_arcs = np.linalg.norm(np.diff(donor, axis=1), axis=2).sum(axis=1)
assert np.all(donor_arcs > 0.)
rng = np.random.default_rng(783)
updated = old.astype(np.float64)
t = np.linspace(0., 1., 23)
root_spread = (1. - .80 * smooth(t/.50))[:, None]
# Preserve both root and first segment; smoothly replace the remaining path.
path_blend = smooth((t-t[1])/.20)[None, :, None]
subclumps = []
for guide in guides:
    parents = np.flatnonzero(assignment == guide)
    if parent_roots[parents, 2].max() <= 1.700:
        continue
    positions = parent_roots[parents]
    seeds = [int(np.argmax(positions[:, 2]))]
    for _ in range(min(3, len(parents))-1):
        distance = np.min(np.sum((positions[:, None]-positions[seeds][None])**2, axis=2), axis=1)
        seeds.append(int(np.argmax(distance)))
    groups = np.argmin(np.sum((positions[:, None]-positions[seeds][None])**2, axis=2), axis=1)
    for group, seed in enumerate(seeds):
        members = parents[groups == group]
        if not len(members):
            continue
        ids = (members[:, None]*3+np.arange(3)).ravel()
        center = positions[seed]
        delta = old[ids].astype(np.float64)-roots[ids, None]
        mean_delta = delta.mean(axis=0)
        donor_id = int(rng.integers(len(donor)))
        transported = donor[donor_id] @ (frame(mean_delta) @ frame(donor[donor_id]).T).T
        target_arc = float(np.median(np.linalg.norm(np.diff(delta, axis=1), axis=2).sum(axis=1)))
        transported *= target_arc / donor_arcs[donor_id]
        # Keep the already fitted crown envelope while changing internal phase.
        envelope = float(np.quantile(np.linalg.norm(delta, axis=2).max(axis=1), .95))
        transported *= min(1., envelope*1.05/max(np.linalg.norm(transported, axis=1).max(), 1e-12))
        proposed = center + transported + root_spread[None]*(roots[ids, None]-center)
        normal = np.asarray(tree.find_nearest(Vector(center))[1])
        height = (proposed-roots[ids, None]) @ normal
        proposed += np.maximum(.00012-height, 0.)[:, :, None]*normal
        crown = smooth((roots[ids, 2]-1.700)/.028)[:, None, None]
        updated[ids] = old[ids]+crown*path_blend*(proposed-old[ids])
        subclumps.append({'old_guide': guide, 'strands': len(ids), 'donor': donor_id,
                          'target_arc_m': target_arc})

updated = updated.astype(np.float32)
assert np.isfinite(updated).all()
assert np.array_equal(updated[:, :2], old[:, :2])
assert np.array_equal(updated[roots[:, 2] <= 1.700], old[roots[:, 2] <= 1.700])
displacement = np.linalg.norm(updated-old, axis=2)
report = {'source': bpy.data.filepath, 'applied': bool(APPLY),
          'outer_curves': len(data.curves), 'original_spatial_groups': len(guides),
          'new_crown_subclumps': len(subclumps), 'distinct_donors': len({g['donor'] for g in subclumps}),
          'changed_strands': int(np.count_nonzero(displacement.max(axis=1) > 1e-7)),
          'max_displacement_m': float(displacement.max()),
          'root_and_first_segment_unchanged': True, 'side_paths_unchanged': True,
          'root_uvs_radii_material_attachment_unchanged': True,
          'other_six_grooms_unchanged': True, 'face_shape_keys': 52, 'rig_drivers': 1957,
          'subclump_strand_counts': [g['strands'] for g in subclumps],
          'license': 'licenses/hair-asset-sources.md'}
if APPLY:
    data.position_data.foreach_set('vector', updated.ravel())
    data.update_tag()
    head['v783_crown_subclumps'] = True
    obj['v783_adaptation'] = 'Three spatial subclumps per outer crown guide with distinct licensed Bystedt paths; roots and first segments retained'
assert all(fingerprint(name) == before[name] for name in other_grooms)
assert np.array_equal(values(data.attributes['surface_uv_coordinate'], 'vector', 2), uvs)
assert np.array_equal(values(data.attributes['radius'], 'value'), radii)
assert list(data.materials) == materials and obj.modifiers['Follow native face and FACS'].node_group == attachment
assert len(head.data.shape_keys.key_blocks) == 52 and len(rig.animation_data.drivers) == 1957
(OUT / 'v783_crown_subclumps.json').write_text(json.dumps(report, indent=2)+'\n')
if APPLY:
    bpy.ops.wm.save_as_mainfile(filepath=str((OUT / 'V783_crown_subclumps_trial.blend').resolve()), compress=True)
if APPLY and RENDER:
    camera = json.loads((ROOT / 'references/derived/photoreal_facebuilder_v1/fitted_camera_v761.json').read_text())
    base = {'EXTRA_OBJECTS': [obj.name]+other_grooms,
            'EXCLUDE_OBJECTS': ['V740_NATIVE_CURLS', 'V740_NATIVE_UNDERCOAT', 'V740_BROW_FIBERS', 'V740_BEARD_FIBERS'],
            'PRESERVE_MATERIALS': True, 'RESOLUTION': tuple(camera['size']),
            'SAMPLES': 128, 'ADAPTIVE_THRESHOLD': .02, 'DENOISE': True}
    for tag, options in [('v783_crown', {}), ('v783_motion', {
            'HEAD_TURN_DEGREES': 12., 'POSE': {'Blink.L': .65, 'Blink.R': .65}})]:
        runpy.run_path(str(ROOT / 'pipeline/render_v740_cloud_groom.py'), init_globals={
            **base, **options, 'CAMERA_RECORD': camera, 'TAG': tag, 'VIEWS': ['reference_orientation']})
        rendered = json.loads((ROOT / 'results' / (tag+'_render_report.json')).read_text())
        assert rendered['production_unchanged'] and rendered['head_basis_restored']
        assert rendered['rig_drivers'] == 1957
print('CROWN_SUBCLUMPS_COMPLETE', json.dumps({k: v for k, v in report.items() if k != 'subclump_strand_counts'}), flush=True)
