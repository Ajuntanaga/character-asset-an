"""A reversible central-face fit from the retained three-view head geometry."""
import json
import math
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree


KEY = 'V560_ReferenceCentralFace'


def smooth(t):
    t = max(0., min(1., t))
    return t * t * (3. - 2. * t)


def field(chin_weight=1.):
    body = bpy.data.objects['V416_BODY_CLEAN_JOIN']
    donor = bpy.data.objects['V376_FACE_PHOTO_DONOR']
    # Use the established V377/V381 registration, not an independent re-fit.
    source_z = [-1.72, -.85, -.30, .0515203, .33, .52, .80, .94, 1.3065]
    target_z = [1.435, 1.521, 1.571, 1.609121, 1.645, 1.670, 1.709, 1.732, 1.795]
    coords = []
    for vertex in donor.data.shape_keys.key_blocks['Basis'].data:
        p = donor.matrix_world @ vertex.co
        coords.append(Vector((.123 * p.x + .0016, .121 * p.y + .00802,
                              float(np.interp(p.z, source_z, target_z)))))
    bvh = BVHTree.FromPolygons(coords, [tuple(p.vertices) for p in donor.data.polygons])
    basis = body.data.shape_keys.key_blocks['Basis']
    lid_slots = {i for i, mat in enumerate(body.data.materials)
                 if mat and mat.name.startswith('V365_LID_SKIN')}
    excluded = {v for p in body.data.polygons if p.material_index in lid_slots
                for v in p.vertices}
    displacements, raw = {}, []
    for i, vertex in enumerate(basis.data):
        if i in excluded:
            continue
        p = body.matrix_world @ vertex.co
        if abs(p.x) > .080 or not 1.504 < p.z < 1.680 or p.y > -.025:
            continue
        nose = math.hypot((p.x - .0016) / .038, (p.z - 1.616) / .043)
        chin = math.hypot((p.x - .0016) / .058, (p.z - 1.539) / .030)
        weight = max(smooth((1.25 - nose) / .65),
                     chin_weight * smooth((1.15 - chin) / .50))
        weight *= smooth((-.025 - p.y) / .025)
        # Keep all lid boundaries and the separate lip/oral seam stationary.
        for cx in (.038, -.0355):
            eye = math.hypot((p.x - cx) / .030, (p.z - 1.645) / .019)
            weight *= smooth((eye - 1.) / .35)
        mouth = math.hypot((p.x + .0005) / .041, (p.z - 1.571) / .016)
        weight *= smooth((mouth - 1.12) / .38)
        if weight < 1e-5:
            continue
        hit, normal, _, _ = bvh.ray_cast(Vector((p.x, -.4, p.z)), Vector((0, 1, 0)))
        if hit is None or abs(hit.y - p.y) > .035:
            continue
        weight *= smooth((-normal.y - .03) / .15)
        if weight < 1e-5:
            continue
        dy = hit.y - p.y
        # Eight millimetres is a trial safety cap, not a claimed fit residual.
        displacements[i] = .008 * math.tanh(dy / .008) * weight
        raw.append(dy * 1000.)
    assert len(displacements) > 100, 'No useful central-face donor overlap'
    report = {
        'source': donor.name, 'body': body.name,
        'registration': 'V377_V381_existing_photo_projection',
        'affected_vertices': len(displacements), 'excluded_lid_vertices': len(excluded),
        'raw_depth_delta_mm_percentiles': np.percentile(raw, [0, 10, 50, 90, 100]).tolist(),
        'key_peak_displacement_mm': max(abs(d) for d in displacements.values()) * 1000.,
        'direction': 'world_Y_only', 'maximum_unweighted_displacement_mm': 8.,
        'scope': 'nose_and_central_chin; eyelids_and_lip_seam_excluded',
        'chin_weight': chin_weight,
    }
    return body, displacements, report


def build(output, chin_weight=1.):
    body, displacements, report = field(chin_weight=chin_weight)
    keys = body.data.shape_keys.key_blocks
    assert KEY not in keys, 'Apply the reversible face fit only once'
    basis = keys['Basis']
    key = body.shape_key_add(name=KEY, from_mix=False)
    key.value = 0.
    key.slider_min, key.slider_max = 0., 1.
    direction = body.matrix_world.inverted().to_3x3() @ Vector((0, 1, 0))
    for i, dy in displacements.items():
        key.data[i].co = basis.data[i].co + direction * dy
    key.value = .75
    body.data.update()
    bpy.context.view_layer.update()
    report.update({'shape_key': KEY, 'trial_value': key.value,
                   'trial_peak_displacement_mm': report['key_peak_displacement_mm'] * key.value,
                   'status': 'REVERSIBLE_TRIAL_REQUIRES_FRONT_PROFILE_REVIEW'})
    (Path(output) / 'face-shape-report.json').write_text(json.dumps(report, indent=2))
    return report
