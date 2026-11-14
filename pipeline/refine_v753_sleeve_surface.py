"""Reversible posed sleeve fairing; requires neutral and wrist-pose review."""
import bpy


def build():
    body = bpy.data.objects['V416_BODY_CLEAN_JOIN']
    rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
    bone = rig.pose.bones['DEF-Forearm_2.L']
    wrist = rig.matrix_world @ bone.tail
    elbowward = rig.matrix_world @ bone.head - wrist
    assert elbowward.length > .01
    axis = elbowward.normalized()
    jacket, other = set(), set()
    for face in body.data.polygons:
        (jacket if face.material_index == 6 else other).update(face.vertices)
    group_names = {g.index: g.name for g in body.vertex_groups}
    states = [(m, m.show_viewport) for m in body.modifiers]
    evaluated = None
    selected = {}
    try:
        for modifier, _ in states:
            modifier.show_viewport = modifier.type == 'ARMATURE'
        bpy.context.view_layer.update()
        evaluated = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh = evaluated.to_mesh()
        assert len(mesh.vertices) == len(body.data.vertices)
        for i in jacket - other:
            influence = sum(g.weight for g in body.data.vertices[i].groups
                            if group_names[g.group] in
                            ('DEF-Forearm_1.L', 'DEF-Forearm_2.L', 'DEF-Hand.L'))
            if influence < .8:
                continue
            offset = evaluated.matrix_world @ mesh.vertices[i].co - wrist
            axial = offset.dot(axis)
            radial = (offset - axial * axis).length
            if not (-.04 < axial < .22 and radial < .14):
                continue
            # Fade spatially at every selection boundary, avoiding a hard ring.
            fade = min(1., (axial + .04) / .04, (.22 - axial) / .08,
                       (.14 - radial) / .04, (influence - .8) / .15)
            fade = max(0., fade)
            selected[i] = fade * fade * (3. - 2. * fade)
    finally:
        if evaluated is not None:
            evaluated.to_mesh_clear()
        for modifier, visible in states:
            modifier.show_viewport = visible
        bpy.context.view_layer.update()
    assert selected, 'No sleeve vertices selected'
    group = body.vertex_groups.new(name='V753_SLEEVE_FAIRING')
    for i, weight in selected.items():
        group.add([i], weight, 'REPLACE')
    modifier = body.modifiers.new('V753 posed sleeve fairing', 'SMOOTH')
    modifier.vertex_group = group.name
    modifier.factor = .65
    modifier.iterations = 12
    index = max(i for i, m in enumerate(body.modifiers) if m.type == 'ARMATURE') + 1
    body.modifiers.move(len(body.modifiers) - 1, index)
    bpy.context.view_layer.update()
    return {'status': 'UNACCEPTED_SURFACE_TRIAL', 'vertices': len(selected),
            'factor': modifier.factor, 'iterations': modifier.iterations,
            'source_coordinates_modified': False,
            'risk': 'Smoothing may reduce sleeve volume; inspect all wrist poses.'}
