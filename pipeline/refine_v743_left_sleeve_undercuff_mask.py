"""Reversible sleeve containment trial; requires wrist seam render review."""
import bpy
from collections import Counter
from mathutils import Vector


def build(cuff, overlap=.006, radial_limit=.16):
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
            modifier.show_viewport = (modifier.type == 'ARMATURE' or
                                      modifier.name == 'V753 posed sleeve fairing')
        bpy.context.view_layer.update()
        evaluated = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh = evaluated.to_mesh()
        assert len(mesh.vertices) == len(body.data.vertices)
        # Diagnose the current evaluated sleeve, including vertices omitted by
        # the weight/material filters. Earlier rest-space sections are not
        # sufficient to explain the visible posed seam.
        nearby = Counter()
        radial_bins = {}
        nearby_vertices = {}
        for i in jacket:
            offset = evaluated.matrix_world @ mesh.vertices[i].co - centers[0]
            axial = offset.dot(axis)
            radial = (offset - axial * axis).length
            if -.22 < axial < .12 and radial < .16:
                inside = -.12 < axial < limit and radial < radial_limit
                reason = ('outside_mask_volume' if not inside else
                          'selected' if i in candidates else
                          'shared_material' if i in other else 'weight_filter')
                nearby[reason] += 1
                nearby_vertices[str(i)] = {
                    'position': list(evaluated.matrix_world @ mesh.vertices[i].co),
                    'selection': reason, 'axial_m': axial, 'radial_m': radial,
                    'weights': {body.vertex_groups[g.group].name: g.weight
                                for g in body.data.vertices[i].groups if g.weight > 0},
                }
                bucket = str(round(axial / .005) * 5)
                row = radial_bins.setdefault(bucket, {'count': 0,
                    'radial_min_mm': float('inf'), 'radial_max_mm': 0.,
                    'excluded_by_weight': 0, 'shared_material': 0,
                    'outside_mask_volume': 0})
                row['outside_mask_volume'] += reason == 'outside_mask_volume'
                row['count'] += 1
                row['radial_min_mm'] = min(row['radial_min_mm'], radial * 1000)
                row['radial_max_mm'] = max(row['radial_max_mm'], radial * 1000)
                row['excluded_by_weight'] += reason == 'weight_filter'
                row['shared_material'] += reason == 'shared_material'
        removed = []
        for i in candidates:
            offset = evaluated.matrix_world @ mesh.vertices[i].co - centers[0]
            axial = offset.dot(axis)
            radial = (offset - axial * axis).length
            if -.12 < axial < limit and radial < radial_limit:
                removed.append(i)
        # Export the actual surviving jacket edge, not only axial summaries.
        # This small report supports a remote sleeve-transition repair without
        # loading the scene or rendering on the workstation. MASK keeps faces
        # whose vertices all survive; count their edges before shell/subsurf.
        removed_set = set(removed)
        kept_edges = Counter()
        removed_edges = Counter()
        for face in mesh.polygons:
            if face.material_index != 6:
                continue
            target = (removed_edges if any(i in removed_set for i in face.vertices)
                      else kept_edges)
            indices = list(face.vertices)
            for a, b in zip(indices, indices[1:] + indices[:1]):
                target[tuple(sorted((a, b)))] += 1
        all_boundary_edges = [edge for edge, uses in kept_edges.items() if uses == 1]
        adjacency = {}
        for a, b in all_boundary_edges:
            adjacency.setdefault(a, set()).add(b)
            adjacency.setdefault(b, set()).add(a)
        # Follow whole connected boundaries; candidate-only edges truncate loops.
        reached = set(adjacency) & candidates
        pending = list(reached)
        while pending:
            vertex = pending.pop()
            for neighbor in adjacency[vertex] - reached:
                reached.add(neighbor)
                pending.append(neighbor)
        boundary_edges = [edge for edge in all_boundary_edges if edge[0] in reached]
        boundary_indices = sorted({i for edge in boundary_edges for i in edge})
        # A surviving boundary is a mask interface only when an incident
        # jacket face was removed. Original openings are not seam anchors.
        interface_edges = [edge for edge in all_boundary_edges
                           if removed_edges[edge]]
        interface_indices = sorted({i for edge in interface_edges for i in edge})
        # Use only retained jacket faces; skin and removed sleeve faces must
        # not tilt the overlap tangent. Compute in world space for scaling.
        source_normals = {i: Vector() for i in interface_indices}
        source_inward = {i: Vector() for i in interface_indices}
        for face in mesh.polygons:
            if face.material_index != 6 or any(i in removed_set for i in face.vertices):
                continue
            hits = set(face.vertices) & source_normals.keys()
            if not hits:
                continue
            corners = [evaluated.matrix_world @ mesh.vertices[i].co for i in face.vertices]
            normal = sum(((corners[j] - corners[0]).cross(corners[j+1] - corners[0])
                          for j in range(1, len(corners)-1)), Vector())
            centroid = sum(corners, Vector()) / len(corners)
            for i in hits:
                source_normals[i] += normal
                source_inward[i] += centroid - evaluated.matrix_world @ mesh.vertices[i].co
        assert all(n.length > 1e-12 for n in source_normals.values())
        interface = {
            'classification': 'retained_jacket_edge_adjacent_to_removed_jacket_face',
            'space': 'world_m',
            'edges': interface_edges,
            # Compare split-seam identity before and after posed smoothing.
            'base_vertices_object_m': {str(i): list(body.data.vertices[i].co)
                                       for i in interface_indices},
            'retained_surface_normals': {str(i): list(n.normalized()) for i, n in source_normals.items()},
            'retained_surface_inward': {str(i): list(v) for i, v in source_inward.items()},
            'vertices': {str(i): list(evaluated.matrix_world @ mesh.vertices[i].co)
                         for i in interface_indices},
            'weights': {str(i): {body.vertex_groups[g.group].name: g.weight
                                 for g in body.data.vertices[i].groups}
                        for i in interface_indices},
            'original_boundary_edges_excluded': sum(not removed_edges[e] for e in boundary_edges),
            'seam_accepted': False,
        }
        boundary = {
            'space': 'world_m',
            'nearby_jacket_vertices': nearby_vertices,
            'nearby_jacket_faces': [list(face.vertices) for face in mesh.polygons
                                    if face.material_index == 6 and
                                    all(str(i) in nearby_vertices for i in face.vertices)],
            'stage': 'deformation_and_optional_fairing_before_mask_shell_and_subdivision',
            'edges': boundary_edges,
            'vertices': {str(i): list(evaluated.matrix_world @ mesh.vertices[i].co)
                         for i in boundary_indices},
            'wrist_center': list(centers[0]),
            'cuff_proximal_center': list(centers[1]),
        }
        rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
        boundary['bones'] = {
            name: {'head': list(rig.matrix_world @ rig.pose.bones[name].head),
                   'tail': list(rig.matrix_world @ rig.pose.bones[name].tail)}
            for name in ('DEF-Hand.L', 'DEF-Forearm_2.L')}
    finally:
        if evaluated is not None:
            evaluated.to_mesh_clear()
        for modifier, visible in states:
            modifier.show_viewport = visible
        bpy.context.view_layer.update()
    assert 0 < len(removed) < len(candidates), (len(removed), len(candidates))
    # The prior 90mm cut left displaced jacket panels around the fingers.
    # Widen only the existing weighted jacket region; keep proximal overlap.
    removed_set = set(removed)
    keep = body.vertex_groups.new(name=name)
    keep.add([v.index for v in body.data.vertices if v.index not in removed_set], 1., 'REPLACE')
    modifier = body.modifiers.new('V743 sleeve under cuff trial', 'MASK')
    modifier.vertex_group = keep.name
    modifier.threshold = .5
    # Run after deformation and before subdivision/shell modifiers.
    index = max(i for i, m in enumerate(body.modifiers) if m.type == 'ARMATURE' or m.name == 'V753 posed sleeve fairing') + 1
    body.modifiers.move(len(body.modifiers) - 1, index)
    return {'status': 'TRIAL_REQUIRES_SEAM_AND_WRIST_MOTION_REVIEW',
            'removed_vertices': len(removed), 'candidate_vertices': len(candidates),
            'nearby_jacket_selection': dict(nearby),
            'surviving_jacket_boundary': boundary,
            'mask_cut_interface': interface,
            'nearby_jacket_axial_bins_mm': radial_bins,
            'overlap_m': overlap, 'radial_limit_m': radial_limit,
            'selection_axis': list(axis),
            'shape_keys': [k.name for k in body.data.shape_keys.key_blocks],
            'source_topology_and_key_coordinates_modified': False,
            'modifier': modifier.name}
