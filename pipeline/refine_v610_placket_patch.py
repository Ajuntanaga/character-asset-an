"""Boundary-constrained removal of fused scan buttons, before new snap covers."""

def build():
    import bpy
    import numpy as np
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree

    body = bpy.data.objects['V416_BODY_CLEAN_JOIN']
    basis = body.data.shape_keys.key_blocks['Basis']
    assert 'V610_PlacketPatch' not in body.data.shape_keys.key_blocks
    evaluated = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    try:
        mesh.calc_loop_triangles()
        posed = [v.co.copy() for v in mesh.vertices]
        tree = BVHTree.FromPolygons(posed, [tuple(t.vertices) for t in mesh.loop_triangles], all_triangles=True)
    finally:
        evaluated.to_mesh_clear()
    adjacency = [set() for _ in posed]
    membership = [set() for _ in posed]
    for edge in body.data.edges:
        a, b = edge.vertices
        adjacency[a].add(b); adjacency[b].add(a)
    for polygon in body.data.polygons:
        for i in polygon.vertices:
            membership[i].add(polygon.material_index)
    key = body.shape_key_add(name='V610_PlacketPatch', from_mix=False)
    report = []
    for px, py in [(254, 256), (249, 392), (240, 530)]:
        x = (px-320)*.4956/640
        z = 1.29+(320-py)*.4956/640
        hit, _, _, _ = tree.ray_cast(Vector((x,-1,z)), Vector((0,1,0)), 1.2)
        assert hit is not None
        faces = [p for p in body.data.polygons if p.material_index == 0
                 and all((posed[i].x-x)**2+(posed[i].z-z)**2 < .020**2
                         and abs(posed[i].y-hit.y) < .025 for i in p.vertices)]
        assert faces
        original = {i for p in faces for i in p.vertices}
        # Include one cloth ring, but never cross into the floral shirt.
        patch = original | {j for i in original for j in adjacency[i]
                            if membership[j] == {6}}
        boundary = {i for i in patch if adjacency[i]-patch or 7 in membership[i]}
        interior = sorted(patch-boundary)
        assert boundary and interior and len(interior) < 1000
        index = {v: j for j, v in enumerate(interior)}
        matrix = np.zeros((len(interior),len(interior)))
        rhs = np.zeros(len(interior))
        for i in interior:
            row = index[i]
            matrix[row,row] = len(adjacency[i])
            for j in adjacency[i]:
                if j in index:
                    matrix[row,index[j]] -= 1
                else:
                    rhs[row] += basis.data[j].co.y
        solved = np.linalg.solve(matrix,rhs)
        displacements = []
        for i, y in zip(interior, solved):
            delta = float(y)-basis.data[i].co.y
            assert abs(delta) < .012, ('displacement limit',px,py,i,delta)
            key.data[i].co.y = float(y)
            displacements.append(abs(delta))
        for polygon in faces:
            polygon.material_index = 6
        report.append({'pixel':[px,py], 'scan_faces':len(faces),
                       'interior_vertices':len(interior), 'fixed_boundary_vertices':len(boundary),
                       'max_displacement_mm':max(displacements)*1000})
    key.value = 1.
    bpy.context.view_layer.update()
    return {'shape_key':key.name,'patches':report,'status':'TRIAL_PENDING_VISUAL_REVIEW'}
