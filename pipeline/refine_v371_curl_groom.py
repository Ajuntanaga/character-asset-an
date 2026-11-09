"""Soften the scanned hair underlay and fill the sparse first strand groom."""
from pathlib import Path
import importlib.util
import json
import math

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'production_v371_curl_groom'
OUT.mkdir(exist_ok=True)
body = bpy.data.objects['V357_TRIPO_CHARACTER_BODY_BOUND']
rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
assert len(rig.animation_data.drivers) == 1957
mask = json.loads((ROOT/'production_v370_curl_groom/hair_mask.json').read_text())
face_ids = set(mask['faces'])
mesh = body.data
n = len(mesh.vertices)
basis = mesh.shape_keys.key_blocks['Basis']
xyz = np.empty(n*3, dtype=np.float32)
basis.data.foreach_get('co', xyz)
xyz = xyz.reshape(-1, 3)
old = mesh.attributes.get('V371_PreScalp')
if old is not None:
    before = np.empty(n*3, dtype=np.float32)
    old.data.foreach_get('vector', before)
    before = before.reshape(-1, 3)
else:
    before = xyz.copy()
    old = mesh.attributes.new('V371_PreScalp', 'FLOAT_VECTOR', 'POINT')
    old.data.foreach_set('vector', before.ravel())

inside = np.zeros(n, dtype=bool)
boundary = np.zeros(n, dtype=bool)
for f in mesh.polygons:
    if f.index in face_ids:
        inside[list(f.vertices)] = True
    else:
        boundary[list(f.vertices)] = True
fixed = ~inside | boundary
# The scan has coincident vertices at UV seams. Move those vertices together:
# independent smoothing tears the scalp along its UV islands.
_, groups = np.unique(np.round(before*1e5).astype(np.int64), axis=0,
                      return_inverse=True)
group_counts = np.bincount(groups)
group_fixed = np.zeros(len(group_counts), dtype=bool)
np.logical_or.at(group_fixed, groups, fixed)
fixed = group_fixed[groups]
edge_array = np.empty(len(mesh.edges)*2, dtype=np.int32)
mesh.edges.foreach_get('vertices', edge_array)
edges = edge_array.reshape(-1, 2)
edges = edges[inside[edges].any(axis=1)]
src = np.concatenate((edges[:, 0], edges[:, 1]))
dst = np.concatenate((edges[:, 1], edges[:, 0]))
counts = np.bincount(src, minlength=n).clip(1)
smooth = before.copy()
for _ in range(50):
    sums = np.zeros_like(smooth)
    np.add.at(sums, src, smooth[dst])
    smooth[~fixed] = .45*smooth[~fixed] + .55*(sums/counts[:, None])[~fixed]
    for axis in range(3):
        averaged = np.bincount(groups, weights=smooth[:, axis])/group_counts
        smooth[~fixed, axis] = averaged[groups[~fixed]]
offset = smooth-before
length = np.linalg.norm(offset, axis=1).clip(1e-9)
smooth = before + offset*np.minimum(1., .0025/length)[:, None]
delta = smooth-xyz
for shape in mesh.shape_keys.key_blocks:
    coords = np.empty(n*3, dtype=np.float32)
    shape.data.foreach_get('co', coords)
    coords = coords.reshape(-1, 3) + delta
    shape.data.foreach_set('co', coords.ravel())
mesh.vertices.foreach_set('co', smooth.ravel())
mesh.update()
rig.update_tag()
bpy.context.view_layer.update()

previous = bpy.data.objects.get('V370_CURL_GROOM')
if previous:
    previous.hide_render = True
    previous.hide_set(True)
data = json.loads((ROOT/'production_v370_curl_groom/scalp_surface.json').read_text())
data['source'] = 'V370 scalp softened only within the hair mask'
data['vertices'] = {key: smooth[int(key)].tolist() for key in data['vertices']}
for f in data['faces']:
    f['normal'] = list(mesh.polygons[f['id']].normal)
(OUT/'scalp_surface.json').write_text(json.dumps(data))
(OUT/'hair_mask.json').write_text(json.dumps(mask))
movement = np.linalg.norm(smooth-before, axis=1)
report = {'vertices_changed': int(np.count_nonzero(movement > 1e-7)),
          'max_underlay_movement_mm': float(movement.max()*1000),
          'mean_underlay_movement_mm': float(movement[inside].mean()*1000),
          'fixed_hair_boundary_vertices': int(np.count_nonzero(inside & boundary))}

spec = importlib.util.spec_from_file_location('groom', ROOT/'pipeline/build_v370_surface_curl_groom.py')
groom = importlib.util.module_from_spec(spec)
spec.loader.exec_module(groom)
rim = bpy.data.objects.get('V347_RIM.004')
if rim:
    rim.data.energy = 180.
groom.main(version=371, target_guides=3500, children=40, melanin=.985,
           roughness=.46, radius_range=(.0032, .0045), clump_width=(.0006, .0011))

head = rig.pose.bones['Head']
curves = bpy.data.objects['V371_CURL_GROOM']
saved_matrix = head.matrix_basis.copy()
saved_mode = head.rotation_mode
initial = curves.matrix_world.copy()
bone_initial = (rig.matrix_world@rig.pose.bones['DEF-Head'].matrix).copy()
try:
    head.rotation_mode = 'XYZ'
    head.rotation_euler.z += math.radians(8)
    rig.update_tag(); bpy.context.view_layer.update()
    expected = rig.matrix_world@rig.pose.bones['DEF-Head'].matrix@bone_initial.inverted()@initial
    report['head_follow_max_matrix_error'] = max(abs(expected[i][j]-curves.matrix_world[i][j])
                                               for i in range(4) for j in range(4))
    assert report['head_follow_max_matrix_error'] < 1e-5
finally:
    head.rotation_mode = saved_mode
    head.matrix_basis = saved_matrix
    rig.update_tag(); bpy.context.view_layer.update()
report['rig_drivers'] = len(rig.animation_data.drivers)
(OUT/'scalp_and_follow_report.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report))
