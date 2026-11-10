"""Opt-in donor wrist continuation; caller owns an isolated trial scene."""
import bmesh
import bpy
from mathutils import Matrix, Vector
from donor_forearm_uv import ForearmUV


def extend_wrist(hand, rig, main, side, length_m=.045, rings=4):
    """Extend the single donor rim toward the forearm with blended weights.

    Does not save, render, or alter the main rig. Cuff fit and appearance still
    require review; this is deliberately not enabled in the production builder.
    """
    assert bpy.context.mode == 'OBJECT'
    assert side in ('L', 'R') and rings >= 2 and 0 < length_m <= .08
    assert len(main.animation_data.drivers) == 1957
    assert hand.data.shape_keys is None, 'Shape-key extension needs explicit handling'
    name = 'V618_ForearmFollow'
    assert name not in rig.data.bones, 'Already extended'
    bm = bmesh.new()
    try:
        bm.from_mesh(hand.data)
        boundary = [e for e in bm.edges if e.is_boundary]
        assert len(boundary) == 28, 'Unexpected donor wrist topology'
        # Reverse the existing boundary face direction for consistent new quads.
        edge = boundary[0]
        loop = next(l for l in edge.link_faces[0].loops if l.edge == edge)
        first, second = loop.link_loop_next.vert, loop.vert
        ordered = [first, second]
        while len(ordered) < len(boundary):
            candidates = [e.other_vert(ordered[-1]) for e in ordered[-1].link_edges
                          if e.is_boundary and e.other_vert(ordered[-1]) != ordered[-2]]
            assert len(candidates) == 1 and candidates[0] not in ordered
            ordered.append(candidates[0])
        assert any(e.other_vert(ordered[-1]) == first for e in ordered[-1].link_edges)
        uv_layer = bm.loops.layers.uv.get('UVMap')
        assert uv_layer is not None, 'Donor atlas UVMap missing'
        atlas = ForearmUV()
        strips = []
        for j, vertex in enumerate(ordered):
            other = ordered[(j + 1) % len(ordered)]
            edge = next(e for e in vertex.link_edges if e.other_vert(vertex) == other)
            source_face = edge.link_faces[0]
            uv_pair = [next(l[uv_layer].uv.copy() for l in source_face.loops if l.vert == v)
                       for v in (vertex, other)]
            chart = atlas.chart_for(vertex.co, uv_pair[0])
            strips.append((chart, uv_pair))
        uv_areas = []
        max_projection_distance = 0.0
        world = rig.matrix_world.copy()
        hand_world = hand.matrix_world.copy()
        center = sum((hand_world @ v.co for v in ordered), Vector()) / len(ordered)
        elbow = main.matrix_world @ main.pose.bones[f'DEF-Forearm_2.{side}'].head
        axis = (elbow - center).normalized()
        old_count = len(bm.verts)
        active = bpy.context.view_layer.objects.active
        selected = list(bpy.context.selected_objects)
        try:
            bpy.ops.object.select_all(action='DESELECT')
            rig.select_set(True)
            bpy.context.view_layer.objects.active = rig
            bpy.ops.object.mode_set(mode='EDIT')
            bone = rig.data.edit_bones.new(name)
            bone.head = (0, 0, 0)
            bone.tail = (0, .1, 0)
            bone.matrix = world.inverted() @ main.matrix_world @ main.pose.bones[f'DEF-Forearm_2.{side}'].matrix
            bpy.ops.object.mode_set(mode='OBJECT')
        finally:
            if bpy.context.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')
            rig.select_set(False)
            for item in selected:
                item.select_set(True)
            bpy.context.view_layer.objects.active = active
        rest = rig.data.bones[name].matrix_local.copy()
        anchor = bpy.data.objects.new(f'V618_WRIST_ANCHOR.{side}', None)
        bpy.context.scene.collection.objects.link(anchor)
        anchor.parent = main
        anchor.parent_type = 'BONE'
        anchor.parent_bone = f'DEF-Forearm_2.{side}'
        anchor.matrix_basis = Matrix.Identity(4)
        anchor.matrix_parent_inverse = Matrix.Identity(4)
        bpy.context.view_layer.update()
        anchor.matrix_parent_inverse = anchor.matrix_world.inverted() @ world @ rest
        anchor.hide_render = True
        anchor.hide_set(True)
        constraint = rig.pose.bones[name].constraints.new('COPY_TRANSFORMS')
        constraint.target = anchor
        constraint.owner_space = constraint.target_space = 'WORLD'
        group = hand.vertex_groups.new(name=name)
        deform = bm.verts.layers.deform.verify()
        weights = [dict(v[deform]) for v in ordered]
        assert all(abs(sum(w.values()) - 1) < .01 for w in weights)
        native_axis = (rig.data.bones['DEF-Hand.R'].head_local -
                       rig.data.bones['DEF-Finger_Middle1.R'].head_local).normalized()
        native_length = length_m / (hand_world.to_3x3() @ native_axis).length
        rim = [hand_world @ v.co for v in ordered]
        inverse = hand_world.inverted()
        previous = ordered
        new_faces = []
        for ring in range(1, rings + 1):
            t = ring / rings
            blend = t * t * (3 - 2 * t)
            current = []
            for point, source_weights in zip(rim, weights):
                v = bm.verts.new(inverse @ (point + axis * (length_m * t) + (point - center) * (.12 * t)))
                for index, weight in source_weights.items():
                    v[deform][index] = weight * (1 - blend)
                v[deform][group.index] = blend
                current.append(v)
            for j in range(len(ordered)):
                k = (j + 1) % len(ordered)
                face = bm.faces.new((previous[j], previous[k], current[k], current[j]))
                chart, prior_uvs = strips[j]
                next_uvs = []
                for index, hint in zip((j, k), prior_uvs):
                    source_point = ordered[index].co + native_axis * (native_length * t)
                    mapped, distance = atlas.sample(source_point, chart, hint)
                    max_projection_distance = max(max_projection_distance, distance)
                    next_uvs.append(mapped)
                quad_uvs = (prior_uvs[0], prior_uvs[1], next_uvs[1], next_uvs[0])
                for loop, mapped in zip(face.loops, quad_uvs):
                    loop[uv_layer].uv = mapped
                area = abs(sum(quad_uvs[i].x * quad_uvs[(i + 1) % 4].y -
                               quad_uvs[(i + 1) % 4].x * quad_uvs[i].y for i in range(4))) * .5
                uv_areas.append(area)
                strips[j] = (chart, next_uvs)
                face.material_index = 0
                face.smooth = True
                new_faces.append(face)
            previous = current
        assert min(uv_areas) > 1e-12, f'Collapsed wrist UV quad: min={min(uv_areas)} max_distance={max_projection_distance}'
        bm.normal_update()
        assert all(face.calc_area() > 1e-12 for face in new_faces)
        assert sum(e.is_boundary for e in bm.edges) == 28
        bm.to_mesh(hand.data)
        hand.data.update()
        bpy.context.view_layer.update()
        deformation = rig.matrix_world @ rig.pose.bones[name].matrix @ rest.inverted() @ world.inverted()
        bind_error = max(abs(deformation[r][c] - float(r == c)) for r in range(4) for c in range(4))
        assert bind_error < 1e-5
        return {'added_vertices': len(hand.data.vertices) - old_count,
                'added_quads': len(new_faces), 'length_m': length_m,
                'uv_min_quad_area': min(uv_areas),
                'uv_max_projection_distance': max_projection_distance,
                'bind_matrix_error': bind_error, 'anchor': anchor.name,
                'status': 'TRIAL_REQUIRES_CUFF_AND_DEFORMATION_REVIEW'}
    finally:
        bm.free()
