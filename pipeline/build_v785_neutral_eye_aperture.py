"""Refine neutral lid aperture; preserve canthi, closed blink, and facial controls."""
import heapq
import json
from collections import Counter
from pathlib import Path
import runpy

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(globals().get('OUT', ROOT / 'results'))
OUT.mkdir(parents=True, exist_ok=True)
RENDER = globals().get('RENDER', True)
head = bpy.data.objects['V740_NATIVE_FACE']
rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
mesh = head.data
keys = mesh.shape_keys.key_blocks
assert head.get('v784_crown_mix') and not head.get('v785_eye_aperture')
assert len(keys) == 52 and len(rig.animation_data.drivers) == 1957
assert all(key.relative_key == keys['Basis'] for key in keys)
original = {}
for key in keys:
    coords = np.empty((len(mesh.vertices), 3), dtype=np.float32)
    key.data.foreach_get('co', coords.ravel())
    original[key.name] = coords
basis = original['Basis']
key_values = {key.name: float(key.value) for key in keys}
grooms = ['V766_ASSET_' + part for part in ('SCALP', 'BROWS', 'BEARD', 'MUSTACHE', 'LASHES')]
grooms += ['V775_SCALP_UNDERCOAT', 'V779_TEMPLE_HAIR']
assert all(name in bpy.data.objects for name in grooms)
camera = json.loads((ROOT / 'references/derived/photoreal_facebuilder_v1/fitted_camera_v761.json').read_text())


def render(tag, **settings):
    runpy.run_path(str(ROOT / 'pipeline/render_v740_cloud_groom.py'), init_globals={
        'EXTRA_OBJECTS': grooms,
        'EXCLUDE_OBJECTS': ['V740_NATIVE_CURLS', 'V740_NATIVE_UNDERCOAT', 'V740_BROW_FIBERS', 'V740_BEARD_FIBERS'],
        'PRESERVE_MATERIALS': True, 'RESOLUTION': tuple(camera['size']),
        'SAMPLES': 128, 'ADAPTIVE_THRESHOLD': .02, 'DENOISE': True,
        'CAMERA_RECORD': camera, 'TAG': tag, 'VIEWS': ['reference_orientation'], **settings})
    rendered = json.loads((ROOT / 'results' / (tag + '_render_report.json')).read_text())
    assert rendered['production_unchanged'] and rendered['head_basis_restored']
    assert rendered['rig_drivers'] == 1957


if RENDER:
    render('v785_baseline')
    render('v785_baseline_front', VIEWS=['front'], CAMERA_RECORD=None)

# Mesh-edge distance prevents influence crossing the open eye. The existing
# blink field separates upper/lower surfaces and tapers the change to the canthi.
edges = Counter(tuple(sorted(edge)) for p in mesh.polygons for edge in p.edge_keys)
boundary = {v for edge, count in edges.items() if count == 1 for v in edge}
adjacency = [[] for _ in basis]
for a, b in edges:
    length = float(np.linalg.norm(basis[a] - basis[b]))
    adjacency[a].append((b, length))
    adjacency[b].append((a, length))
delta = np.zeros_like(basis)
side_vertices = {}
report = {'source': bpy.data.filepath, 'upper_lowering_mm': 1.5, 'lower_lids_unchanged': True,
          'shape_keys': len(keys), 'rig_drivers': len(rig.animation_data.drivers),
          'sides': {}, 'materials_and_eyeballs_unchanged': True}
for side, sign in [('Left', 1), ('Right', -1)]:
    blink_dz = original['eyeBlink' + side][:, 2] - basis[:, 2]
    region = (basis[:, 2] > 1.625) & (basis[:, 2] < 1.665) & (sign * basis[:, 0] > .012) & (sign * basis[:, 0] < .065)
    side_ids = set()
    report['sides'][side] = {}
    for label, direction, amount in [('upper', -1., .0015)]:
        seeds = [i for i in boundary if region[i] and direction * blink_dz[i] > .0005]
        assert 8 < len(seeds) < 35, (side, label, len(seeds))
        eligible = (sign * basis[:, 0] > .010) & (direction * blink_dz > 1e-6)
        weights = np.zeros(len(basis), dtype=np.float64)
        amplitude = float((direction * blink_dz[seeds]).max())
        radius = .008
        for seed in seeds:
            seed_weight = direction * float(blink_dz[seed]) / amplitude
            distances, queue = {seed: 0.}, [(0., seed)]
            while queue:
                distance, index = heapq.heappop(queue)
                if distance > distances[index]:
                    continue
                t = 1. - distance / radius
                weights[index] = max(weights[index], seed_weight * t * t * (3. - 2. * t))
                for neighbor, length in adjacency[index]:
                    candidate = distance + length
                    if eligible[neighbor] and candidate < min(radius, distances.get(neighbor, radius)):
                        distances[neighbor] = candidate
                        heapq.heappush(queue, (candidate, neighbor))
        ids = np.flatnonzero(weights > 1e-6)
        assert len(seeds) < len(ids) < 700
        delta[ids, 2] += direction * amount * weights[ids]
        # Move the narrowed margins forward slightly to follow the convex eye.
        delta[ids, 1] -= .00025 * weights[ids]
        side_ids.update(ids.tolist())
        report['sides'][side][label] = {'boundary_vertices': len(seeds), 'affected_vertices': len(ids),
                                      'maximum_displacement_mm': float(np.linalg.norm(delta[ids], axis=1).max() * 1000)}
    side_vertices[side] = np.asarray(sorted(side_ids), dtype=np.int32)

# Retain absolute full-blink targets, while transporting other expressions with
# the neutral edit. This keeps the existing control names and relative-key basis.
for key in keys:
    changed = original[key.name] + delta
    for side, ids in side_vertices.items():
        if key.name == 'eyeBlink' + side:
            changed[ids] = original[key.name][ids]
    key.data.foreach_set('co', changed.ravel())
mesh.vertices.foreach_set('co', (basis + delta).ravel())
mesh.update()

# Translate existing lash curves by root-UV-interpolated rest displacement.
# Shape, radii and root UVs remain intact; native surface deformation still runs.
mesh.calc_loop_triangles()
triangles = np.asarray([t.vertices[:] for t in mesh.loop_triangles], dtype=np.int32)
affected = np.any(np.linalg.norm(delta[triangles], axis=2) > 0, axis=1)
uv_layer = mesh.uv_layers['UVMap']
uv = np.asarray([[uv_layer.data[i].uv[:] for i in t.loops] for t in mesh.loop_triangles])[affected]
triangles = triangles[affected]
a, ab, ac = uv[:, 0], uv[:, 1] - uv[:, 0], uv[:, 2] - uv[:, 0]
denominator = ab[:, 0] * ac[:, 1] - ab[:, 1] * ac[:, 0]
assert (np.abs(denominator) > 1e-15).all()
patch = basis[np.linalg.norm(delta, axis=1) > 0]
low, high = patch.min(0) - .002, patch.max(0) + .002
adjustments = {}
for name in grooms:
    data = bpy.data.objects[name].data
    assert data.surface == head and data.surface_uv_map == 'UVMap'
    assert np.max(np.abs(np.asarray(bpy.data.objects[name].matrix_world) - np.asarray(head.matrix_world))) < 1e-6
    roots = np.asarray([data.position_data[c.first_point_index].vector[:] for c in data.curves])
    candidates = np.flatnonzero(np.all((roots >= low) & (roots <= high), axis=1))
    moved = []
    for index in candidates:
        root_uv = np.asarray(data.attributes['surface_uv_coordinate'].data[int(index)].vector[:])
        ap = root_uv - a
        v = (ap[:, 0] * ac[:, 1] - ap[:, 1] * ac[:, 0]) / denominator
        w = (ab[:, 0] * ap[:, 1] - ab[:, 1] * ap[:, 0]) / denominator
        bary = np.column_stack((1 - v - w, v, w))
        matches = np.flatnonzero(np.all(bary >= -1e-5, axis=1))
        if not len(matches):
            continue
        distances = np.linalg.norm(np.einsum('ij,ijk->ik', bary[matches], basis[triangles[matches]]) - roots[index], axis=1)
        match = matches[int(distances.argmin())]
        assert float(distances.min()) < .002, (name, int(index), float(distances.min()))
        shift = bary[match] @ delta[triangles[match]]
        if np.linalg.norm(shift) < 1e-9:
            continue
        curve = data.curves[int(index)]
        for point in data.position_data[curve.first_point_index:curve.first_point_index + curve.points_length]:
            point.vector = np.asarray(point.vector) + shift
        moved.append(float(np.linalg.norm(shift)))
    if moved:
        data.update_tag()
    adjustments[name] = {'curves_moved': len(moved), 'maximum_mm': max(moved, default=0.) * 1000}
assert adjustments['V766_ASSET_LASHES']['curves_moved'] > 20
assert all(not adjustments[name]['curves_moved'] for name in grooms if name != 'V766_ASSET_LASHES')
report['groom_root_adjustments'] = adjustments
updated = {}
for name in ['Basis', 'eyeBlinkLeft', 'eyeBlinkRight']:
    values = np.empty_like(basis)
    keys[name].data.foreach_get('co', values.ravel())
    updated[name] = values
closed_before = original['eyeBlinkLeft'] + original['eyeBlinkRight'] - basis
closed_after = updated['eyeBlinkLeft'] + updated['eyeBlinkRight'] - updated['Basis']
error = float(np.abs(closed_after - closed_before).max())
assert error < 3e-7, error
report['closed_blink_coordinate_max_error_m'] = error
assert len(keys) == 52 and len(rig.animation_data.drivers) == 1957
assert {key.name: float(key.value) for key in keys} == key_values
head['v785_eye_aperture'] = True
head.update_tag(refresh={'DATA'})
bpy.context.view_layer.update()
report['checkpoint'] = str((OUT / 'V785_neutral_eye_aperture_trial.blend').resolve())
(OUT / 'v785_eye_aperture.json').write_text(json.dumps(report, indent=2) + '\n')
bpy.ops.wm.save_as_mainfile(filepath=report['checkpoint'], compress=True)
if RENDER:
    render('v785_candidate')
    render('v785_candidate_front', VIEWS=['front'], CAMERA_RECORD=None)
    render('v785_half_blink', VIEWS=['front'], CAMERA_RECORD=None, POSE={'Blink.L': .5, 'Blink.R': .5},
           RESOLUTION=(960, 1200), BORDER=(.18, .82, .42, .65))
    render('v785_closed', VIEWS=['front'], CAMERA_RECORD=None, POSE={'Blink.L': 1., 'Blink.R': 1.},
           RESOLUTION=(960, 1200), BORDER=(.18, .82, .42, .65))
print('NEUTRAL_EYE_APERTURE_COMPLETE', json.dumps(report), flush=True)
