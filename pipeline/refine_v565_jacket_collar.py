"""Narrow and flatten the scanned jacket collar with a reversible shape key."""
import json
import math
from pathlib import Path


KEY = 'V565_ReferenceJacketCollar'


def smooth(t):
    t = min(1., max(0., t))
    return t * t * (3. - 2. * t)


def displacement(x, y, z):
    ax = abs(x)
    # Continuous spatial falloff keeps coincident scan/UV seams together.
    # Limit the field to the front collar wings, above the chest/lapel folds.
    w = smooth((ax - .055) / .030) * (1. - smooth((ax - .170) / .025))
    w *= smooth((z - 1.372) / .030) * (1. - smooth((z - 1.490) / .035))
    w *= smooth((-.009 - y) / .028) * (1. - smooth((-y - .074) / .024))
    if w < 1e-7:
        return (0., 0., 0.)
    # Bring the oversized wings toward the opening without moving the shirt.
    dx = -math.copysign(.30 * (ax - .055) * w, x)
    # Flatten the inflated outer fold onto a sloping cloth plane. The falloff
    # keeps the collar stand, rear jacket and underlying chest stationary.
    plane_y = -.044 + .28 * (ax - .100) + .32 * (z - 1.440)
    dy = .55 * (plane_y - y) * w
    tip = math.exp(-((ax - .145) / .022) ** 2 - ((z - 1.405) / .016) ** 2)
    dz = -.004 * tip * w
    return (dx, dy, dz)


def build(output):
    import bpy
    from mathutils import Vector

    body = bpy.data.objects['V416_BODY_CLEAN_JOIN']
    assert body.data.attributes.get('V372_RestPosition') is not None
    slots = {i for i, m in enumerate(body.data.materials)
             if m and m.name in {'V379_DARK_COTTON_JACKET',
                                 'V561_MATTE_CHARCOAL_CHECK_JACKET'}}
    assert len(slots) == 1, f'Unexpected jacket slots: {slots}'
    indices = {i for p in body.data.polygons if p.material_index in slots
               for i in p.vertices}
    keys = body.data.shape_keys.key_blocks
    assert KEY not in keys, 'Apply the collar trial only once'
    basis = keys['Basis']
    key = body.shape_key_add(name=KEY, from_mix=False)
    key.value = 0.
    world_to_local = body.matrix_world.inverted().to_3x3()
    moved, peak = 0, 0.
    for i in indices:
        p = body.matrix_world @ basis.data[i].co
        delta = Vector(displacement(*p))
        if delta.length < 1e-8:
            continue
        key.data[i].co = basis.data[i].co + world_to_local @ delta
        moved += 1
        peak = max(peak, delta.length)
    assert 100 < moved < 12000, f'Unexpected collar coverage: {moved}'
    key.value = 1.
    body.data.update()
    bpy.context.view_layer.update()
    assert len(bpy.data.objects['V357_CLOUDRIG_CONTROLS'].animation_data.drivers) == 1957
    report = {'body': body.name, 'shape_key': KEY, 'trial_value': key.value,
              'affected_vertices': moved, 'peak_displacement_mm': peak * 1000.,
              'jacket_material_slots': sorted(slots),
              'rest_position_attribute_preserved': True,
              'status': 'REVERSIBLE_TRIAL_REQUIRES_COLLAR_RENDER_REVIEW'}
    (Path(output) / 'collar-shape-report.json').write_text(json.dumps(report, indent=2))
    return report
