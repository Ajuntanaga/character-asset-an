"""Lengthen the licensed short beard, retaining roots and face attachments."""
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
RENDER = globals().get('RENDER', True)
head = bpy.data.objects['V740_NATIVE_FACE']
rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
assert head.get('v784_crown_mix') and not head.get('v785_eye_aperture')
assert not head.get('v787_short_beard')
assert len(head.data.shape_keys.key_blocks) == 52 and len(rig.animation_data.drivers) == 1957
grooms = ['V766_ASSET_' + part for part in ('SCALP', 'BROWS', 'BEARD', 'MUSTACHE', 'LASHES')]
grooms += ['V775_SCALP_UNDERCOAT', 'V779_TEMPLE_HAIR']
beard = bpy.data.objects['V766_ASSET_BEARD']
data = beard.data


def values(collection, prop, width=1):
    array = np.empty((len(collection), width), np.float32)
    collection.foreach_get(prop, array.ravel())
    return array


def fingerprint(name):
    curves = bpy.data.objects[name].data
    return hashlib.sha256(b''.join(array.tobytes() for array in [
        values(curves.position_data, 'vector', 3),
        values(curves.attributes['radius'].data, 'value'),
        values(curves.attributes['surface_uv_coordinate'].data, 'vector', 2)])).hexdigest()


def smooth(value):
    value = np.clip(value, 0., 1.)
    return value * value * (3. - 2. * value)


before = {name: fingerprint(name) for name in grooms if name != beard.name}
old = values(data.position_data, 'vector', 3)
radii = values(data.attributes['radius'].data, 'value')
uvs = values(data.attributes['surface_uv_coordinate'].data, 'vector', 2)
counts = np.array([len(curve.points) for curve in data.curves], np.int32)
offsets = np.r_[0, np.cumsum(counts)]
assert counts.min() >= 2
roots = old[offsets[:-1]]
# Fuller chin/jaw, lighter cheeks and a feathered neck boundary.
factors = 1. + (.35 + .80 * smooth((1.602 - roots[:, 2]) / .065)) * smooth((roots[:, 2] - 1.514) / .012)
coords = values(head.data.shape_keys.key_blocks['Basis'].data, 'co', 3)
head.data.calc_loop_triangles()
triangles = [triangle.vertices[:] for triangle in head.data.loop_triangles]
surface = BVHTree.FromPolygons(coords.tolist(), triangles, all_triangles=True)
updated = old.copy()
lengths_before, lengths_after, corrections = [], [], []
minimum_clearance = float('inf')
retained_for_clearance = 0
for i, (start, end) in enumerate(zip(offsets[:-1], offsets[1:])):
    path = old[start:end].astype(np.float64)
    lengths_before.append(np.linalg.norm(np.diff(path, axis=0), axis=1).sum())
    # The three two-point donor strands have no tip beyond the retained segment.
    if len(path) == 2:
        lengths_after.append(lengths_before[-1])
        continue
    arc = np.r_[0., np.cumsum(np.linalg.norm(np.diff(path, axis=0), axis=1))]
    blend = smooth((arc - arc[1]) / max(arc[-1] - arc[1], 1e-9))
    path += (path - path[0]) * ((factors[i] - 1.) * blend[:, None])
    strand_margin, strand_corrections = float('inf'), []
    for j in range(2, len(path)):
        point = Vector(path[j])
        original = point.copy()
        clearance = float(radii[start+j, 0]) + .00003
        # Near jaw triangle boundaries the nearest face can change after a push.
        for _ in range(24):
            hit, normal, _, _ = surface.find_nearest(point)
            signed = (point - hit).dot(normal)
            if signed >= clearance - 1e-7:
                break
            point += normal * (clearance - signed + .000002)
        hit, normal, _, _ = surface.find_nearest(point)
        strand_margin = min(strand_margin, (point - hit).dot(normal) - clearance)
        path[j] = point
        strand_corrections.append((point - original).length)
    if strand_margin < -2e-6 or max(strand_corrections) > .001:
        # Preserve the complete original path instead of forcing it around a crease.
        retained_for_clearance += 1
        lengths_after.append(lengths_before[-1])
        continue
    minimum_clearance = min(minimum_clearance, strand_margin)
    corrections.extend(strand_corrections)
    updated[start:end] = path
    lengths_after.append(np.linalg.norm(np.diff(path, axis=0), axis=1).sum())
assert np.isfinite(updated).all()
assert np.array_equal(updated[offsets[:-1]], old[offsets[:-1]])
assert np.array_equal(updated[offsets[:-1] + 1], old[offsets[:-1] + 1])
assert minimum_clearance >= -2e-6, minimum_clearance
assert retained_for_clearance <= len(counts) * .01, retained_for_clearance
assert max(lengths_after) < .011, max(lengths_after)
data.position_data.foreach_set('vector', updated.ravel())
data.update_tag()
assert np.array_equal(values(data.attributes['radius'].data, 'value'), radii)
assert np.array_equal(values(data.attributes['surface_uv_coordinate'].data, 'vector', 2), uvs)
assert all(fingerprint(name) == checksum for name, checksum in before.items())
assert data.surface == head and data.surface_uv_map == 'UVMap'
head['v787_short_beard'] = True
beard['v787_adaptation'] = 'Licensed Einar paths lengthened toward the chin; roots, first segments, UVs and radii retained.'
bpy.context.view_layer.update()
report = {'source': bpy.data.filepath, 'beard_curves': len(counts),
          'two_point_strands_retained': int(np.count_nonzero(counts == 2)),
          'original_strands_retained_for_clearance': retained_for_clearance,
          'length_percentiles_mm_before': (np.percentile(lengths_before, [0, 10, 50, 90, 100]) * 1000).tolist(),
          'length_percentiles_mm_after': (np.percentile(lengths_after, [0, 10, 50, 90, 100]) * 1000).tolist(),
          'roots_first_segments_uvs_radii_unchanged': True, 'other_six_grooms_unchanged': True,
          'max_surface_correction_mm': max(corrections) * 1000,
          'minimum_changed_point_clearance_margin_m': minimum_clearance,
          'face_shape_keys': 52, 'rig_drivers': 1957,
          'facial_shader_v786': bool(head.get('v786_facial_hair_shading')),
          'license': 'licenses/hair-asset-sources.md',
          'checkpoint': str((OUT / 'V787_short_beard_trial.blend').resolve())}
(OUT / 'v787_short_beard.json').write_text(json.dumps(report, indent=2) + '\n')
bpy.ops.wm.save_as_mainfile(filepath=report['checkpoint'], compress=True)
if RENDER:
    camera = json.loads((ROOT / 'references/derived/photoreal_facebuilder_v1/fitted_camera_v761.json').read_text())
    for tag, view, pose in [('v787_beard_front', 'front', {}),
                            ('v787_beard_reference', 'reference_orientation', {}),
                            ('v787_beard_jaw_open', 'reference_orientation', {'JawOpen': .45})]:
        runpy.run_path(str(ROOT / 'pipeline/render_v740_cloud_groom.py'), init_globals={
            'EXTRA_OBJECTS': grooms,
            'EXCLUDE_OBJECTS': ['V740_NATIVE_CURLS', 'V740_NATIVE_UNDERCOAT', 'V740_BROW_FIBERS', 'V740_BEARD_FIBERS'],
            'PRESERVE_MATERIALS': True, 'RESOLUTION': tuple(camera['size']),
            'SAMPLES': 128, 'ADAPTIVE_THRESHOLD': .02, 'DENOISE': True,
            'CAMERA_RECORD': camera if view == 'reference_orientation' else {},
            'TAG': tag, 'VIEWS': [view], 'POSE': pose})
        rendered = json.loads((ROOT / 'results' / (tag + '_render_report.json')).read_text())
        assert rendered['production_unchanged'] and rendered['head_basis_restored']
        assert rendered['rig_drivers'] == 1957
print('SHORT_BEARD_COMPLETE', json.dumps(report), flush=True)
