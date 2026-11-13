"""Reversible sleeve containment trial; requires wrist seam render review."""
import bpy
from mathutils import Vector


def build(cuff, overlap=.006):
    body = bpy.data.objects['V416_BODY_CLEAN_JOIN']
    name = 'V743_KEEP_OUTSIDE_UNDERCUFF'
    assert body.vertex_groups.get(name) is None
    count = len(cuff.data.vertices) // 5
    assert count * 5 == len(cuff.data.vertices)
    centers = [cuff.matrix_world @ (sum((v.co for v in
               cuff.data.vertices[j * count:(j + 1) * count]), Vector()) / count)
               for j in (0, 4)]
    axis = (centers[1] - centers[0]).normalized()
    limit = (centers[1] - centers[0]).length - overlap
    groups = {body.vertex_groups[n].index for n in ('DEF-Hand.L', 'DEF-Forearm_2.L')}
    candidates = {v.index for v in body.data.vertices
                  if any(g.group in groups and g.weight > .2 for g in v.groups)}
    # Reject vertices shared with skin or other material regions.
    jacket = set()
    other = set()
    for face in body.data.polygons:
        (jacket if face.material_index == 6 else other).update(face.vertices)
    candidates &= jacket - other
    # Evaluate only deformation modifiers so base indices remain meaningful.
    states = [(m, m.show_viewport) for m in body.modifiers]
    evaluated = None
    try:
        for modifier, _ in states:
            modifier.show_viewport = modifier.type == 'ARMATURE'
        bpy.context.view_layer.update()
        evaluated = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh = evaluated.to_mesh()
        assert len(mesh.vertices) == len(body.data.vertices)
        removed = []
        for i in candidates:
            offset = evaluated.matrix_world @ mesh.vertices[i].co - centers[0]
            axial = offset.dot(axis)
            radial = (offset - axial * axis).length
            if -.12 < axial < limit and radial < .09:
                removed.append(i)
    finally:
        if evaluated is not None:
            evaluated.to_mesh_clear()
        for modifier, visible in states:
            modifier.show_viewport = visible
        bpy.context.view_layer.update()
    assert 0 < len(removed) < len(candidates), (len(removed), len(candidates))
    removed_set = set(removed)
    keep = body.vertex_groups.new(name=name)
    keep.add([v.index for v in body.data.vertices if v.index not in removed_set], 1., 'REPLACE')
    modifier = body.modifiers.new('V743 sleeve under cuff trial', 'MASK')
    modifier.vertex_group = keep.name
    modifier.threshold = .5
    # Run after deformation and before subdivision/shell modifiers.
    index = max(i for i, m in enumerate(body.modifiers) if m.type == 'ARMATURE') + 1
    body.modifiers.move(len(body.modifiers) - 1, index)
    return {'status': 'TRIAL_REQUIRES_SEAM_AND_WRIST_MOTION_REVIEW',
            'removed_vertices': len(removed), 'candidate_vertices': len(candidates),
            'overlap_m': overlap, 'selection_axis': list(axis),
            'shape_keys': [k.name for k in body.data.shape_keys.key_blocks],
            'source_topology_and_key_coordinates_modified': False,
            'modifier': modifier.name}
