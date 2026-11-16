"""Lower the neutral upper-lid arc while preserving absolute closed-blink targets."""
import heapq
import json
import runpy
from collections import Counter
from pathlib import Path

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parent
OUT = Path(globals().get('OUTPUT_DIR', 'results'))
OUT.mkdir(parents=True, exist_ok=True)
RENDER = globals().get('RENDER', True)
head = bpy.data.objects['V740_NATIVE_FACE']
rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
mesh = head.data
keys = mesh.shape_keys.key_blocks
assert not head.get('v768_upper_lid_trial'), 'This trial must start from V767'
assert len(mesh.vertices) == 18024 and len(mesh.polygons) == 17188
assert len(keys) == 52 and len(rig.animation_data.drivers) == 1957
assert all(key.relative_key == keys['Basis'] for key in keys)
key_values = {key.name: float(key.value) for key in keys}
original = {}
for key in keys:
    values = np.empty((len(mesh.vertices), 3), dtype=np.float32)
    key.data.foreach_get('co', values.ravel())
    original[key.name] = values
basis = original['Basis']
installed = ['V766_ASSET_' + part for part in ('SCALP', 'BROWS', 'BEARD', 'MUSTACHE', 'LASHES')]
excluded = ['V740_NATIVE_CURLS', 'V740_NATIVE_UNDERCOAT', 'V740_BROW_FIBERS', 'V740_BEARD_FIBERS']
camera = json.loads((ROOT.parent / 'references/derived/photoreal_facebuilder_v1/fitted_camera_v761.json').read_text())
render_base = {'EXTRA_OBJECTS': installed, 'EXCLUDE_OBJECTS': excluded,
               'PRESERVE_MATERIALS': True, 'RESOLUTION': tuple(camera['size']),
               'SAMPLES': 128, 'ADAPTIVE_THRESHOLD': .02, 'DENOISE': True}
blink_view = {'VIEWS': ['front'], 'POSE': {'Blink.L': 1., 'Blink.R': 1.},
              'RESOLUTION': (960, 1200), 'BORDER': (.18, .82, .42, .65)}

def render(tag, **settings):
    runpy.run_path(str(ROOT / 'render_v740_cloud_groom.py'), init_globals={
        **render_base, **settings, 'TAG': tag})

if RENDER:
    render('v768_baseline_closed', **blink_view)

# Follow mesh edges, not Euclidean proximity across the open eye. The blink
# field identifies the upper surface and excludes the lower lid and canthi.
edge_counts = Counter(tuple(sorted(edge)) for p in mesh.polygons for edge in p.edge_keys)
boundary = {v for edge, count in edge_counts.items() if count == 1 for v in edge}
adjacency = [[] for _ in mesh.vertices]
for a, b in edge_counts:
    length = float(np.linalg.norm(basis[a] - basis[b]))
    adjacency[a].append((b, length))
    adjacency[b].append((a, length))
delta = np.zeros_like(basis)
side_vertices = {}
report = {'source': bpy.data.filepath, 'revision': '1.2 mm neutral upper-lid arc with closed targets retained',
          'shape_keys': len(keys), 'rig_drivers': len(rig.animation_data.drivers),
          'sides': {}, 'groom_root_adjustments': {}}
radius = .008
for side, sign in [('Left', 1), ('Right', -1)]:
    blink_dz = original['eyeBlink' + side][:, 2] - basis[:, 2]
    seeds = [i for i in boundary if 1.625 < basis[i, 2] < 1.665
             and .012 < sign * basis[i, 0] < .065 and blink_dz[i] < -.0005]
    assert len(seeds) == 22, (side, len(seeds))
    eligible = (sign * basis[:, 0] > .010) & (blink_dz < -1e-6)
    weights = np.zeros(len(basis), dtype=np.float64)
    amplitude = -float(blink_dz[seeds].min())
    for seed in seeds:
        seed_weight = -float(blink_dz[seed]) / amplitude
        distances = {seed: 0.}
        queue = [(0., seed)]
        while queue:
            distance, index = heapq.heappop(queue)
            if distance > distances[index]:
                continue
            t = 1. - distance / radius
            weights[index] = max(weights[index], seed_weight * t * t * (3. - 2. * t))
            for neighbor, length in adjacency[index]:
                candidate = distance + length
                if eligible[neighbor] and candidate < radius and candidate < distances.get(neighbor, radius):
                    distances[neighbor] = candidate
                    heapq.heappush(queue, (candidate, neighbor))
    ids = np.flatnonzero(weights > 1e-6)
    assert 22 < len(ids) < 700, (side, len(ids))
    delta[ids, 2] = -.0012 * weights[ids]
    # A small anterior displacement keeps the lowered rim outside the cornea.
    delta[ids, 1] = -.0002 * weights[ids]
    side_vertices[side] = ids
    report['sides'][side] = {'upper_boundary_vertices': len(seeds), 'affected_vertices': len(ids),
                           'max_lowering_mm': float(-delta[ids, 2].min() * 1000),
                           'max_anterior_mm': float(-delta[ids, 1].min() * 1000)}

for key in keys:
    changed = original[key.name] + delta
    for side, ids in side_vertices.items():
        if key.name == 'eyeBlink' + side:
            changed[ids] = original[key.name][ids]
    key.data.foreach_set('co', changed.ravel())
mesh.vertices.foreach_set('co', (basis + delta).ravel())
mesh.update()

# Curves are stored in the head's rest coordinates. Move an affected curve by
# its root's UV-interpolated neutral displacement; its strand shape is retained.
mesh.calc_loop_triangles()
triangles = np.asarray([t.vertices[:] for t in mesh.loop_triangles], dtype=np.int32)
affected = np.any(np.linalg.norm(delta[triangles], axis=2) > 0, axis=1)
uv_layer = mesh.uv_layers['UVMap']
uv = np.asarray([[uv_layer.data[i].uv[:] for i in t.loops] for t in mesh.loop_triangles])[affected]
triangles = triangles[affected]
a, ab, ac = uv[:, 0], uv[:, 1] - uv[:, 0], uv[:, 2] - uv[:, 0]
denom = ab[:, 0] * ac[:, 1] - ab[:, 1] * ac[:, 0]
valid = np.abs(denom) > 1e-15
assert valid.all(), 'Affected UV triangles must be nondegenerate'
patch = basis[np.linalg.norm(delta, axis=1) > 0]
low, high = patch.min(0) - .002, patch.max(0) + .002
for name in installed:
    obj = bpy.data.objects[name]
    data = obj.data
    assert data.surface == head and data.surface_uv_map == 'UVMap'
    assert np.max(np.abs(np.asarray(obj.matrix_world) - np.asarray(head.matrix_world))) < 1e-6
    roots = np.asarray([data.position_data[c.first_point_index].vector[:] for c in data.curves])
    candidates = np.flatnonzero(np.all((roots >= low) & (roots <= high), axis=1))
    moved = []
    for index in candidates:
        root_uv = np.asarray(data.attributes['surface_uv_coordinate'].data[index].vector[:])
        ap = root_uv - a
        v = (ap[:, 0] * ac[:, 1] - ap[:, 1] * ac[:, 0]) / denom
        w = (ab[:, 0] * ap[:, 1] - ab[:, 1] * ap[:, 0]) / denom
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
    data.update_tag()
    report['groom_root_adjustments'][name] = {'curves_moved': len(moved),
        'maximum_mm': max(moved, default=0.) * 1000}
assert report['groom_root_adjustments']['V766_ASSET_LASHES']['curves_moved'] > 20

# Both closed-blink coordinates must be invariant, including simultaneous blink.
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
assert {key.name: float(key.value) for key in keys} == key_values
assert len(rig.animation_data.drivers) == 1957
head['v768_upper_lid_trial'] = True
head.update_tag(refresh={'DATA'})
bpy.context.view_layer.update()

if RENDER:
    render('v768_neutral', VIEWS=['reference_orientation'], CAMERA_RECORD=camera)
    render('v768_neutral_front', VIEWS=['front'])
    render('v768_closed', **blink_view)
assert {key.name: float(key.value) for key in keys} == key_values
output = Path(globals().get('SAVE_FILE', OUT / 'V768_upper_lid_trial.blend')).resolve()
bpy.ops.wm.save_as_mainfile(filepath=str(output), compress=True)
report['checkpoint'] = str(output)
report['checkpoint_bytes'] = output.stat().st_size
(OUT / 'v768_upper_lid_trial.json').write_text(json.dumps(report, indent=2))
print('UPPER_LID_TRIAL_COMPLETE', json.dumps(report), flush=True)
