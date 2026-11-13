"""Isolated, unpromoted cuff trial fitted to the evaluated donor wrist.

Run after V545 hand construction. No save, render, or source deletion.
The sleeve overlap and motion remain subject to visual review.
"""
import bmesh
import bpy
from mathutils import Matrix, Vector


def build(clearance=.002, length=.040):
    main = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
    hand = bpy.data.objects['V545_NATIVE_HAND.L']
    source = bpy.data.objects['V357_CUFF_PATCH.L']
    name = 'V742_WRIST_FITTED_CUFF.L'
    assert name not in bpy.data.objects
    assert .001 <= clearance <= .004 and .02 <= length <= .06
    evaluated = hand.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    bm = bmesh.new()
    try:
        bm.from_mesh(mesh)
        edges = [e for e in bm.edges if e.is_boundary]
        assert edges, 'Donor wrist is closed or absent'
        vertices = {v for e in edges for v in e.verts}
        assert all(sum(e.is_boundary for e in v.link_edges) == 2 for v in vertices)
        first = min(vertices, key=lambda v: v.index)
        ordered = [first]
        previous = None
        current = first
        while True:
            choices = [e.other_vert(current) for e in current.link_edges
                       if e.is_boundary and e.other_vert(current) != previous]
            nxt = min(choices, key=lambda v: v.index)
            if nxt == first:
                break
            assert nxt not in ordered
            ordered.append(nxt)
            previous, current = current, nxt
        assert len(ordered) == len(vertices), 'Multiple donor boundary loops'
        rim = [evaluated.matrix_world @ v.co for v in ordered]
    finally:
        bm.free()
        evaluated.to_mesh_clear()
    center = sum(rim, Vector()) / len(rim)
    elbow = main.matrix_world @ main.pose.bones['DEF-Forearm_2.L'].head
    # Fit the opening normal to the donor boundary, not the elbow direction:
    # a bent wrist can make projection onto the forearm collapse the opening.
    import numpy as np
    offsets = np.array([tuple(p - center) for p in rim])
    _, singular, basis = np.linalg.svd(offsets, full_matrices=False)
    assert singular[1] > .005, f'Degenerate donor rim: {singular.tolist()}'
    axis = Vector(basis[-1])
    if axis.dot(elbow - center) < 0:
        axis.negate()
    bone_world = main.matrix_world @ main.pose.bones['DEF-Hand.L'].matrix
    location, rotation, _ = bone_world.decompose()
    frame = Matrix.LocRotScale(location, rotation, Vector((1, 1, 1)))
    inverse = frame.inverted()
    # The donor rim determines the cross-section, including its asymmetry.
    radial = [p - center - axis * (p - center).dot(axis) for p in rim]
    assert min(v.length for v in radial) > .005, f'Rim radii: {[v.length for v in radial]}'
    points = []
    count = len(rim)
    for t in (0., .08, .5, .92, 1.):
        for original, offset in zip(rim, radial):
            world = original + axis * (length * t) + offset * (.18 * t) + offset.normalized() * clearance
            points.append(inverse @ world)
    faces = [(j * count + i, j * count + (i + 1) % count,
              (j + 1) * count + (i + 1) % count, (j + 1) * count + i)
             for j in range(4) for i in range(count)]
    data = bpy.data.meshes.new(name)
    data.from_pydata(points, [], faces)
    data.update()
    bm = bmesh.new()
    try:
        bm.from_mesh(data)
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        bm.to_mesh(data)
    finally:
        bm.free()
    uv = data.uv_layers.new(name='UVMap')
    # The inherited V441/V445 box-projected weave reads this attribute,
    # not UVMap. Store metric coordinates so the weave follows the cuff.
    rest = data.attributes.new('V441_CuffRest', 'FLOAT_VECTOR', 'POINT')
    for vertex, value in zip(data.vertices, rest.data):
        value.vector = vertex.co
    ring_parameters = (0., .08, .5, .92, 1.)
    for polygon in data.polygons:
        columns = [data.loops[i].vertex_index % count for i in polygon.loop_indices]
        seam = 0 in columns and count - 1 in columns
        for loop_index in polygon.loop_indices:
            vertex_index = data.loops[loop_index].vertex_index
            column = vertex_index % count
            u = 1. if seam and column == 0 else column / count
            uv.data[loop_index].uv = (u, ring_parameters[vertex_index // count])
    cuff = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(cuff)
    for material in source.data.materials:
        cuff.data.materials.append(material)
    for polygon in cuff.data.polygons:
        polygon.use_smooth = True
    # No parent and no armature: bone scale is deliberately excluded.
    for kind in ('COPY_LOCATION', 'COPY_ROTATION'):
        constraint = cuff.constraints.new(kind)
        constraint.target = main
        constraint.subtarget = 'DEF-Hand.L'
        constraint.owner_space = constraint.target_space = 'WORLD'
    solid = cuff.modifiers.new('Fabric thickness', 'SOLIDIFY')
    solid.thickness = .0015
    solid.offset = 1.
    bpy.context.view_layer.update()
    error = max(abs(cuff.matrix_world[r][c] - frame[r][c])
                for r in range(4) for c in range(4))
    assert error < 1e-5, f'Unexpected cuff binding frame: {error}'
    return cuff, {'status': 'TRIAL_REQUIRES_RENDER_AND_MOTION_REVIEW',
                  'rim_samples': count, 'clearance_m': clearance,
                  'opening_axis': list(axis),
                  'minimum_radius_m': min(v.length for v in radial),
                  'length_m': length, 'binding_error': error,
                  'fabric_rest_attribute': 'V441_CuffRest',
                  'source_preserved': True, 'scale_inheritance': False}
