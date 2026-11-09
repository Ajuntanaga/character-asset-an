"""Reduce the scanned rear collar roll with a continuous reversible field."""
import json
from pathlib import Path


KEY = 'V584_RearCollarFlatten'


def smooth(t):
    t = min(1., max(0., t))
    return t * t * (3. - 2. * t)


def displacement(x, y, z):
    # Fade into the shoulder cloth; the diagnostic mesh was cropped at 1.465 m
    # and cannot be treated as a disconnected collar component.
    weight = smooth((z - 1.445) / .035)
    weight *= 1. - smooth((z - 1.545) / .020)
    weight *= 1. - smooth((abs(x) - .140) / .050)
    weight *= smooth((y - .020) / .040)
    return 0., -.65 * max(0., y - .085) * weight, 0.


def build(output):
    import bpy
    from mathutils import Vector

    body = bpy.data.objects['V416_BODY_CLEAN_JOIN']
    assert body.data.attributes.get('V372_RestPosition') is not None
    slots = {i for i, material in enumerate(body.data.materials)
             if material and material.name == 'V561_MATTE_CHARCOAL_CHECK_JACKET'}
    assert len(slots) == 1, slots
    indices = {i for face in body.data.polygons if face.material_index in slots
               for i in face.vertices}
    keys = body.data.shape_keys.key_blocks
    assert KEY not in keys, 'Apply the rear collar trial only once'
    basis = keys['Basis']
    key = body.shape_key_add(name=KEY, from_mix=False)
    # Basis may differ from stale mesh coordinates after earlier rebuild stages.
    for target, source in zip(key.data, basis.data):
        target.co = source.co
    key.value = 0.
    to_local = body.matrix_world.inverted().to_3x3()
    moved, peak = 0, 0.
    for index in indices:
        point = body.matrix_world @ basis.data[index].co
        delta = Vector(displacement(*point))
        if delta.length < 1e-8:
            continue
        key.data[index].co = basis.data[index].co + to_local @ delta
        moved += 1
        peak = max(peak, delta.length)
    assert 100 < moved < 12000, moved
    assert peak < .040, peak
    key.value = 1.
    body.data.update()
    bpy.context.view_layer.update()
    assert len(bpy.data.objects['V357_CLOUDRIG_CONTROLS'].animation_data.drivers) == 1957
    report = {'shape_key': KEY, 'value': key.value, 'affected_vertices': moved,
              'peak_displacement_mm': peak * 1000.,
              'field': 'rear jacket only, continuous fade into shoulders',
              'rest_position_attribute_preserved': True,
              'status': 'REVERSIBLE_TRIAL_REQUIRES_REAR_AND_OBLIQUE_REVIEW'}
    (Path(output) / 'rear-collar-shape-report.json').write_text(json.dumps(report, indent=2))
    return report
