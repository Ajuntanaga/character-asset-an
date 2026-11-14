"""Reversible open sleeve panel; fit through the actual armature deformation."""
import bpy
from mathutils import Vector, Matrix
from pathlib import Path
import runpy


def build(cuff, interface):
    body = bpy.data.objects['V416_BODY_CLEAN_JOIN']
    source_mod = next(m for m in body.modifiers if m.type == 'ARMATURE')
    assert source_mod.use_vertex_groups and not source_mod.use_bone_envelopes
    assert not source_mod.vertex_group, 'Masked armature needs explicit transfer'
    points = {int(k): Vector(v) for k, v in interface['vertices'].items()}
    weights = {int(k): v for k, v in interface['weights'].items()}
    # Co-located split-seam endpoints are merged only in this new object.
    canonical = {}
    for i in sorted(points):
        canonical[i] = next((j for j in canonical if canonical[j] == j
                            and (points[i] - points[j]).length < 1e-7
                            and weights[i] == weights[j]), i)
    adjacency = {}
    for a, b in interface['edges']:
        a, b = canonical[a], canonical[b]
        if a != b:
            adjacency.setdefault(a, set()).add(b)
            adjacency.setdefault(b, set()).add(a)
    ends = [i for i, neighbors in adjacency.items() if len(neighbors) == 1]
    assert len(ends) == 2 and all(len(n) <= 2 for n in adjacency.values())
    rail, previous, current = [], None, min(ends)
    while current is not None:
        rail.append(current)
        following = adjacency[current] - {previous}
        previous, current = current, next(iter(following), None)
        assert len(rail) <= len(adjacency)
    assert len(rail) == len(adjacency)
    n = len(cuff.data.vertices) // 5
    rim = [cuff.matrix_world @ v.co for v in cuff.data.vertices[4*n:5*n]]
    center = sum(rim, Vector()) / n
    mapper = runpy.run_path(str(Path(__file__).with_name('sleeve_correspondence.py')))
    mapped, correspondence = mapper['ordered_rim_points'](
        [list(points[i]) for i in rail], [list(p) for p in rim])
    inner_points = {i: Vector(p) for i, p in zip(rail, mapped)}
    fair_points = dict(zip(rail, map(Vector, mapper['smooth_open_rail'](
        [list(points[i]) for i in rail]))))

    target, vertex_weights = [], []
    # Open strip: never cap the unrelated original jacket openings.
    rows = (-.15, 0., .2, .4, .6, .8, 1.)
    for t in rows:
        blend = max(0., t)
        for i in rail:
            outer = points[i]
            inner = inner_points[i]
            inner = inner + (center - inner).normalized() * .0015
            direction = inner - outer
            p = (outer - direction.normalized() * .006 if t < 0
                 else outer.lerp(fair_points[i], min(1., t / .2)).lerp(inner, t))
            target.append(p)
            w = {name: value * (1-blend) for name, value in weights[i].items()
                 if name.startswith('DEF-') and value > 0}
            w['DEF-Hand.L'] = w.get('DEF-Hand.L', 0.) + blend
            total = sum(w.values())
            assert total > 0
            vertex_weights.append({name: value / total for name, value in w.items() if value > 0})
    # Sample locally: segmented/bendy bones can make the fixed-weight mapping
    # position dependent. Newton steps fit the actual evaluated deformation.
    mesh = bpy.data.meshes.new('V744 armature fit probes')
    basis = [Vector(), Vector((.001, 0, 0)), Vector((0, .001, 0)), Vector((0, 0, .001))]
    mesh.from_pydata([tuple(p) for _ in target for p in basis], [], [])
    panel = bpy.data.objects.new('V744_LEFT_SLEEVE_UNDERCUFF_PANEL', mesh)
    bpy.context.collection.objects.link(panel)
    panel.matrix_world = body.matrix_world.copy()
    group_names = sorted({name for w in vertex_weights for name in w})
    for name in group_names:
        group = panel.vertex_groups.new(name=name)
        for j, w in enumerate(vertex_weights):
            if name in w:
                group.add(list(range(4*j, 4*j+4)), w[name], 'REPLACE')
    modifier = panel.modifiers.new('V744 source armature', 'ARMATURE')
    modifier.object = source_mod.object
    modifier.use_deform_preserve_volume = source_mod.use_deform_preserve_volume
    modifier.use_vertex_groups = True
    modifier.use_bone_envelopes = False
    inverse_world = panel.matrix_world.inverted()
    desired_local = [inverse_world @ p for p in target]
    rest = [p.copy() for p in desired_local]
    fit_iterations = 0
    for iteration in range(12):
        for j, position in enumerate(rest):
            for k, delta in enumerate(basis):
                mesh.vertices[4*j+k].co = position + delta
        mesh.update()
        panel.update_tag()
        bpy.context.view_layer.update()
        evaluated = panel.evaluated_get(bpy.context.evaluated_depsgraph_get())
        probe = evaluated.to_mesh()
        try:
            residual = 0.
            corrections = []
            for j, desired in enumerate(desired_local):
                origin = probe.vertices[4*j].co.copy()
                difference = desired - origin
                residual = max(residual, (panel.matrix_world.to_3x3() @ difference).length)
                columns = [(probe.vertices[4*j+k].co-origin)/.001 for k in (1,2,3)]
                transform = Matrix(columns).transposed()
                assert abs(transform.determinant()) > 1e-8
                corrections.append(transform.inverted() @ difference)
        finally:
            evaluated.to_mesh_clear()
        fit_iterations = iteration + 1
        if residual < .00001:
            break
        for j, correction in enumerate(corrections):
            # Bound each step near the local derivative sample.
            if correction.length > .05:
                correction = correction.normalized() * .05
            rest[j] += correction
    width = len(rail)
    faces = [(r*width+c, r*width+c+1, (r+1)*width+c+1, (r+1)*width+c)
             for r in range(len(rows)-1) for c in range(width-1)]
    final_mesh = bpy.data.meshes.new('V744 weighted open sleeve panel')
    final_mesh.from_pydata(rest, [], faces)
    final_mesh.materials.append(body.data.materials[6])
    panel.data = final_mesh
    bpy.data.meshes.remove(mesh)
    for group in list(panel.vertex_groups):
        panel.vertex_groups.remove(group)
    for name in group_names:
        group = panel.vertex_groups.new(name=name)
        for j, w in enumerate(vertex_weights):
            if name in w:
                group.add([j], w[name], 'REPLACE')
    bpy.context.view_layer.update()
    evaluated = panel.evaluated_get(bpy.context.evaluated_depsgraph_get())
    fitted = evaluated.to_mesh()
    try:
        error = max((panel.matrix_world @ v.co-p).length for v, p in zip(fitted.vertices, target))
        assert error < .00005, error
    finally:
        evaluated.to_mesh_clear()
    for face in final_mesh.polygons:
        face.use_smooth = True
    shell = panel.modifiers.new('V744 cloth thickness', 'SOLIDIFY')
    shell.thickness = .001
    shell.offset = -1
    return {'status': 'TRIAL_REQUIRES_WRIST_RENDER_REVIEW', 'object': panel.name,
            'rail_vertices': width, 'rows': len(rows), 'bind_max_error_m': error,
            'correspondence': correspondence,
            'source_fairing_radius_m': .012,
            'source_seam_preserved': True,
            'mapping_world_m': {
                'source_rail_vertex_ids': rail,
                'source_rail': [list(points[i]) for i in rail],
                'cuff_rim': [list(p) for p in rim],
                'inset_inner_rail': [list(p) for p in target[-width:]],
            },
            'open_strip': True, 'source_mesh_or_shape_keys_modified': False,
            'fit_iterations': fit_iterations,
            'binding': 'iterative_local_armature_inverse_with_preserve_volume'}
