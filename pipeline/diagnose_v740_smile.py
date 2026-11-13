"""Locate smile surface compression on the remote native-face checkpoint.

This measures deformation, not visual quality or self-intersection acceptance.
It changes no geometry and restores every facial control it touches.
"""
from pathlib import Path
import json
import bpy
import numpy as np

head = bpy.data.objects['V740_NATIVE_FACE']
rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
control = rig.pose.bones['Head']
properties = ['JawOpen', 'Blink.L', 'Blink.R', 'BrowInnerUp',
              'BrowDown.L', 'BrowDown.R', 'BrowOuterUp.L', 'BrowOuterUp.R',
              'Smile.L', 'Smile.R', 'MouthPucker']
saved = {name: control[name] for name in properties}


def surface(amount):
    for name in properties:
        control[name] = amount if name in {'Smile.L', 'Smile.R'} else 0.
    rig.update_tag(refresh={'OBJECT'})
    bpy.context.view_layer.update()
    obj = head.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = obj.to_mesh()
    try:
        mesh.calc_loop_triangles()
        points = np.array([v.co[:] for v in mesh.vertices], dtype=np.float64)
        triangles = np.array([t.vertices[:] for t in mesh.loop_triangles], dtype=np.int32)
        polygon_ids = np.array([t.polygon_index for t in mesh.loop_triangles])
        return points, triangles, polygon_ids, tuple(tuple(p.vertices) for p in mesh.polygons)
    finally:
        obj.to_mesh_clear()


def normals(points, triangles):
    p = points[triangles]
    cross = np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0])
    magnitude = np.linalg.norm(cross, axis=1)
    return cross / np.maximum(magnitude[:, None], 1e-20), magnitude


def compare_lower_face_fit():
    """Compare identical cage triangles before and after the landmark mapping.

    Invert each stored key separately before blending. Inverting an already
    blended expression would incorrectly commute a nonlinear fit with blending.
    Upper-head edits and clamped endpoints are excluded from this comparison.
    """
    keys = head.data.shape_keys.key_blocks
    names = ('Basis', 'mouthSmileLeft', 'mouthSmileRight')
    fitted = [np.array([v.co[:] for v in keys[name].data], dtype=np.float64)
              for name in names]
    for name in names[1:]:
        assert keys[name].relative_key == keys['Basis']
    source_z = np.array([-1.72, -.85, -.30, .0515203, .33, .52, .80, .94, 1.3065])
    target_z = np.array([1.435, 1.521, 1.571, 1.609121, 1.645, 1.670, 1.709, 1.732, 1.795])
    donor = []
    interior = np.ones(len(fitted[0]), dtype=bool)
    for points in fitted:
        interior &= (points[:, 2] > target_z[0] + 1e-6) & (points[:, 2] < 1.645)
        restored = points.copy()
        restored[:, 0] = (points[:, 0] - .0016) / .123
        restored[:, 1] = (points[:, 1] - .00802) / .121
        restored[:, 2] = np.interp(points[:, 2], target_z, source_z)
        donor.append(restored * .123)
    head.data.calc_loop_triangles()
    triangles = np.array([t.vertices[:] for t in head.data.loop_triangles], dtype=np.int32)
    centers = fitted[0][triangles].mean(axis=1)
    region = (interior[triangles].all(axis=1) & (abs(centers[:, 0]) < .055)
              & (centers[:, 1] < -.065) & (centers[:, 2] > 1.54)
              & (centers[:, 2] < 1.61))
    triangle_ids = np.flatnonzero(region)
    triangles = triangles[region]
    assert len(triangles), 'Empty mouth comparison region'
    comparisons = {}
    for label, coordinates in [('landmark_fitted', fitted), ('reconstructed_donor_uniform_scale', donor)]:
        rest, left, right = coordinates
        rest_normals, rest_area = normals(rest, triangles)
        valid = rest_area > 1e-12
        samples = []
        for amount in (.2, .4, .6, .8, 1.):
            posed = rest + amount * (left - rest) + amount * (right - rest)
            normal, area = normals(posed, triangles)
            ratio = area / np.maximum(rest_area, 1e-20)
            dot = np.clip(np.sum(normal * rest_normals, axis=1), -1., 1.)
            worst = np.flatnonzero(valid)
            worst = worst[np.argsort(dot[worst])[:12]]
            samples.append({'bilateral_smile': amount,
                'triangles_rotated_over_90_degrees': int(np.sum(valid & (dot < 0))),
                'triangles_below_one_fifth_rest_area': int(np.sum(valid & (ratio < .2))),
                'worst_rotation_triangles': [{'cage_triangle': int(triangle_ids[i]),
                    'cage_vertices': triangles[i].tolist(),
                    'fitted_rest_center': centers[triangle_ids[i]].tolist(),
                    'area_ratio': float(ratio[i]),
                    'normal_rotation_degrees': float(np.degrees(np.arccos(dot[i])))} for i in worst]})
        comparisons[label] = samples
    return {'scope': 'Unsubdivided mouth cage only; inverse fit reconstructed from stored keys, '
                     'not an independently loaded donor. Rotation is not a collision test.',
            'triangle_count': len(triangles), 'comparisons': comparisons}


records = []
try:
    basis, triangles, polygon_ids, topology = surface(0.)
    base_normal, base_area = normals(basis, triangles)
    valid = base_area > 1e-12
    assert valid.any(), 'No nondegenerate triangles'
    for amount in (.2, .4, .6, .8, 1.):
        points, _, _, current_topology = surface(amount)
        assert points.shape == basis.shape
        assert current_topology == topology, 'Evaluated topology changed'
        # Keep rest triangulation fixed: n-gon tessellation may change with pose.
        normal, area = normals(points, triangles)
        ratio = area / np.maximum(base_area, 1e-20)
        dot = np.clip(np.sum(normal * base_normal, axis=1), -1., 1.)
        # Include coordinates and IDs so a repair can be localized without
        # assuming that every compressed triangle is a defective mouth corner.
        ids = np.flatnonzero(valid)
        selected = sorted(set(ids[np.argsort(ratio[ids])[:20]].tolist() +
                              ids[np.argsort(dot[ids])[:20]].tolist()))
        records.append({
            'bilateral_smile': amount,
            'triangles_below_one_fifth_rest_area': int(np.sum(valid & (ratio < .2))),
            'triangles_rotated_over_90_degrees': int(np.sum(valid & (dot < 0.))),
            'maximum_vertex_displacement_m': float(np.linalg.norm(points - basis, axis=1).max()),
            'extreme_triangles': [{
                'triangle': int(i), 'polygon': int(polygon_ids[i]),
                'vertices': triangles[i].tolist(),
                'rest_center_local': basis[triangles[i]].mean(axis=0).tolist(),
                'posed_center_local': points[triangles[i]].mean(axis=0).tolist(),
                'area_ratio': float(ratio[i]),
                'normal_rotation_degrees': float(np.degrees(np.arccos(dot[i]))),
            } for i in selected],
        })
finally:
    for name, value in saved.items():
        control[name] = value
    rig.update_tag(refresh={'OBJECT'})
    bpy.context.view_layer.update()

out = Path('results')
out.mkdir(exist_ok=True)
(out / 'smile_surface_diagnostic.json').write_text(json.dumps({
    'scope': 'Evaluated native face, five static bilateral smile levels. '
             'Area compression and normal rotation are diagnostic signals, not '
             'proof of inversion, collision, source cause, or animation acceptance.',
    'degenerate_rest_triangles_excluded': int(np.sum(~valid)),
    'controls_restored': all(control[name] == value for name, value in saved.items()),
    'samples': records,
    'lower_face_fit_comparison': compare_lower_face_fit(),
}, indent=2))
