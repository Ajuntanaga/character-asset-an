"""Transfer the retained donor's pucker and keep the beard on the moving skin."""
import json
from pathlib import Path


def build(output):
    import bpy
    import numpy as np
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    from mathutils.geometry import barycentric_transform

    name = 'MouthPucker'
    rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
    head = rig.pose.bones['Head']
    body = bpy.data.objects['V416_BODY_CLEAN_JOIN']
    lips = bpy.data.objects['V363_LIPS']
    cavity = bpy.data.objects['V363_MOUTH_CAVITY']
    beard = bpy.data.objects['V395_BEARD_FIBERS']
    donor = bpy.data.objects['V376_FACE_PHOTO_DONOR']
    assert len(rig.animation_data.drivers) == 1957
    assert name not in head and name not in body.data.shape_keys.key_blocks
    assert len(lips.data.vertices) == 960 and len(cavity.data.vertices) == 480

    source_z = [-1.72, -.85, -.30, .0515203, .33, .52, .80, .94, 1.3065]
    target_z = [1.435, 1.521, 1.571, 1.609121, 1.645, 1.670, 1.709, 1.732, 1.795]

    def fitted(p):
        return Vector((.123 * p.x + .0016, .121 * p.y + .00802,
                       float(np.interp(p.z, source_z, target_z))))

    def smooth(t):
        t = min(1., max(0., t))
        return t * t * (3. - 2. * t)

    donor_keys = donor.data.shape_keys.key_blocks
    lid_slots = {i for i, mat in enumerate(body.data.materials)
                 if mat and mat.name.startswith('V365_LID_SKIN')}
    excluded = {i for p in body.data.polygons if p.material_index in lid_slots
                for i in p.vertices}
    assert len(excluded) == 1536, f'Unexpected eyelid coverage: {len(excluded)}'
    coords = [fitted(donor.matrix_world @ v.co) for v in donor_keys['Basis'].data]
    donor.data.calc_loop_triangles()
    triangles = [tuple(t.vertices) for t in donor.data.loop_triangles]
    bvh = BVHTree.FromPolygons(coords, triangles, all_triangles=True)
    field = [fitted(donor.matrix_world @ v.co) - p
             for v, p in zip(donor_keys['mouthPucker'].data, coords)]

    def sample(p):
        # The established V381 donor registration, confined below the nose.
        weight = smooth((p.z - 1.50) / .020) * smooth((1.640 - p.z) / .020)
        weight *= smooth((.086 - abs(p.x)) / .016) * smooth((-.022 - p.y) / .040)
        if weight < 1e-5:
            return None
        hit, normal, index, _ = bvh.ray_cast(Vector((p.x, -.4, p.z)), Vector((0, 1, 0)))
        if hit is None or abs(hit.y - p.y) > .042 or normal.y > -.02:
            return None
        ids = triangles[index]
        weights = barycentric_transform(hit, *[coords[i] for i in ids],
                                        Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1)))
        return sum((field[i] * w for i, w in zip(ids, weights)), Vector()) * weight

    def add_key(obj, key_name, deltas, control=True):
        keys = obj.data.shape_keys.key_blocks
        assert key_name not in keys
        key = obj.shape_key_add(name=key_name, from_mix=False)
        basis = keys['Basis']
        inverse = obj.matrix_world.inverted().to_3x3()
        for i, delta in deltas.items():
            key.data[i].co = basis.data[i].co + inverse @ delta
        driver = key.driver_add('value').driver
        driver.type = 'SCRIPTED'
        var = driver.variables.new()
        var.name, var.type = 'v', 'SINGLE_PROP'
        if control:
            var.targets[0].id = rig
            var.targets[0].data_path = f'pose.bones["Head"]["{key_name}"]'
        else:
            var.targets[0].id_type = 'KEY'
            var.targets[0].id = body.data.shape_keys
            var.targets[0].data_path = keys_body[key_name].path_from_id('value')
        driver.expression = 'v'
        obj.data.update()
        return key

    head[name] = 0.
    head.id_properties_ui(name).update(min=0., max=1., description='Round and project the lips')
    deltas = {}
    for obj in (body, lips):
        basis = obj.data.shape_keys.key_blocks['Basis']
        deltas[obj.name] = {i: d for i, v in enumerate(basis.data)
                            if not (obj == body and i in excluded)
                            if (d := sample(obj.matrix_world @ v.co)) is not None}
        peak = max(d.length for d in deltas[obj.name].values())
        assert .0001 < peak < .030, (obj.name, peak)
        add_key(obj, name, deltas[obj.name])
    lip_deltas = deltas[lips.name]
    assert all(i in lip_deltas for i in range(96)), 'Missing lip aperture sample'
    cavity_deltas = {j * 96 + i: lip_deltas[i] * (1. - j * .5)
                     for j in (0, 1) for i in range(96)}
    add_key(cavity, name, cavity_deltas)
    # Exact shared aperture motion prevents a split between lips and oral shell.
    seam_error = max((lips.matrix_world.to_3x3() @ (
        lips.data.shape_keys.key_blocks[name].data[i].co - lips.data.shape_keys.key_blocks['Basis'].data[i].co)
        - cavity.matrix_world.to_3x3() @ (
        cavity.data.shape_keys.key_blocks[name].data[i].co - cavity.data.shape_keys.key_blocks['Basis'].data[i].co)).length
        for i in range(96))
    assert seam_error < 3e-7, seam_error

    # Reattach the existing fibers; do not generate a new beard or change its density.
    keys_body = body.data.shape_keys.key_blocks
    body_coords = [body.matrix_world @ v.co for v in keys_body['Basis'].data]
    body.data.calc_loop_triangles()
    beard_triangles = [tuple(t.vertices) for t in body.data.loop_triangles
                       if all(1.49 < body_coords[i].z < 1.64 and body_coords[i].y < -.020
                              for i in t.vertices)]
    skin = BVHTree.FromPolygons(body_coords, beard_triangles, all_triangles=True)
    attachments = {}
    max_distance = 0.
    for i, v in enumerate(beard.data.shape_keys.key_blocks['Basis'].data):
        p = beard.matrix_world @ v.co
        hit, normal, index, distance = skin.find_nearest(p)
        assert hit is not None
        max_distance = max(max_distance, distance)
        ids = beard_triangles[index]
        weights = barycentric_transform(hit, *[body_coords[j] for j in ids],
                                        Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1)))
        attachments[i] = (ids, weights)
    assert max_distance < .010, f'Beard is too far from the skin: {max_distance}'
    followed = []
    for key_name in (name, 'V560_ReferenceCentralFace'):
        if key_name not in keys_body:
            continue
        source = keys_body[key_name]
        world = body.matrix_world.to_3x3()
        field = [world @ (v.co - b.co) for v, b in zip(source.data, keys_body['Basis'].data)]
        hair_deltas = {i: sum((field[j] * w for j, w in zip(ids, weights)), Vector())
                       for i, (ids, weights) in attachments.items()}
        add_key(beard, key_name, hair_deltas, control=False)
        followed.append(key_name)

    checks = []
    original_jaw = head['JawOpen']
    try:
        for pucker, jaw in ((0., 0.), (.45, 0.), (.45, .2)):
            head[name], head['JawOpen'] = pucker, jaw
            rig.update_tag()
            bpy.context.view_layer.update()
            actual = {obj.name: obj.data.shape_keys.key_blocks[name].value
                      for obj in (body, lips, cavity, beard)}
            assert all(abs(v - pucker) < 1e-6 for v in actual.values()), actual
            checks.append({'pucker': pucker, 'jaw': jaw, 'shape_values': actual})
        for key_name in followed:
            assert abs(beard.data.shape_keys.key_blocks[key_name].value - keys_body[key_name].value) < 1e-6
    finally:
        head[name], head['JawOpen'] = 0., original_jaw
        rig.update_tag()
        bpy.context.view_layer.update()
    assert len(rig.animation_data.drivers) == 1957
    report = {'control': name, 'donor_key': 'mouthPucker', 'rig_drivers': 1957,
              'excluded_lid_vertices': len(excluded),
              'moved_vertices': {k: sum(d.length > 1e-5 for d in values.values()) for k, values in deltas.items()},
              'peak_displacement_mm': {k: max(d.length for d in values.values()) * 1000. for k, values in deltas.items()},
              'cavity_seam_delta_error_mm': seam_error * 1000.,
              'beard_follow_keys': followed, 'beard_max_surface_distance_mm': max_distance * 1000.,
              'driver_checks': checks, 'status': 'TRIAL_REQUIRES_EXPRESSION_RENDER_REVIEW'}
    (Path(output) / 'mouth-pucker-report.json').write_text(json.dumps(report, indent=2))
    return report
