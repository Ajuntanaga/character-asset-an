"""Fair the scanned scalp and use that same surface for the replacement groom."""
from collections import defaultdict
import json
from pathlib import Path

import bpy
import numpy as np


def part_center(y):
    return .040 + .13 * (y + .070) + .0014 * np.sin((y + .105) * 55.)


def part_strength(point):
    x, y, z = point
    if z <= 1.720 or not -.100 < y < -.045:
        return 0.
    ends = min(1., (y + .100) / .010, (-.045 - y) / .010)
    distance = abs(x - part_center(y))
    lane = np.clip((distance - .00025) / .0009, 0., 1.)
    return float(ends * (1. - lane * lane * (3. - 2. * lane)))


def nape_candidate(point):
    x, y, z = point
    if not (1.575 <= z < 1.668 and y >= .035):
        return False
    # Keep the outer ear and lobe bare while following the hair behind them.
    ear = abs(x) > .070 and ((y - .018) / .035) ** 2 + ((z - 1.620) / .043) ** 2 < 1.
    return not ear


def build(output):
    body = bpy.data.objects['V416_BODY_CLEAN_JOIN']
    assert max(abs(body.matrix_world[r][c] - float(r == c))
               for r in range(4) for c in range(4)) < 1e-6
    mesh = body.data
    basis = mesh.shape_keys.key_blocks['Basis'].data
    count = len(mesh.vertices)
    original = np.empty((count, 3), dtype=np.float32)
    basis.foreach_get('co', original.ravel())
    head_faces = [p for p in mesh.polygons if min(original[v, 2] for v in p.vertices) > 1.51]
    ids = np.array(sorted({v for p in head_faces for v in p.vertices}), dtype=np.int32)
    index = {int(v): i for i, v in enumerate(ids)}
    _, groups = np.unique(np.round(original[ids] * 1e5).astype(np.int64), axis=0,
                          return_inverse=True)
    group_count = np.bincount(groups)
    group_xyz = np.stack([np.bincount(groups, weights=original[ids, a]) / group_count
                          for a in range(3)], axis=1)
    hair_index = list(mesh.materials).index(bpy.data.materials['V371_DARK_HAIR_UNDERLAY'])
    skin_indices = {0, list(mesh.materials).index(bpy.data.materials['V377_REFERENCE_PHOTO_SKIN'])}
    edges, adjacency, hair_groups = defaultdict(set), defaultdict(set), set()
    face_groups, face_centers, edge_faces = {}, {}, defaultdict(set)
    original_hair = {p.index for p in head_faces if p.material_index == hair_index}
    candidates = set()
    for polygon in head_faces:
        g = [int(groups[index[v]]) for v in polygon.vertices]
        face_groups[polygon.index] = g
        face_centers[polygon.index] = group_xyz[g].mean(axis=0)
        if polygon.material_index in skin_indices and nape_candidate(face_centers[polygon.index]):
            candidates.add(polygon.index)
        for a, b in zip(g, g[1:] + g[:1]):
            if a != b:
                edge_faces[tuple(sorted((a, b)))].add(polygon.index)
    face_neighbors = defaultdict(set)
    for linked in edge_faces.values():
        for face in linked:
            face_neighbors[face].update(linked - {face})
    seeds = {f for f in candidates if face_neighbors[f] & original_hair}
    assert seeds, 'No posterior hair boundary seed'
    nape_faces = {max(seeds, key=lambda f: (face_centers[f][1], f))}
    stack = list(nape_faces)
    while stack:
        for face in face_neighbors[stack.pop()] & (candidates - nape_faces):
            nape_faces.add(face)
            stack.append(face)
    assert len(nape_faces) > 100, 'No connected posterior scalp extension'
    virtual_hair = original_hair | nape_faces
    for polygon in head_faces:
        g = face_groups[polygon.index]
        kind = ('hair' if polygon.index in virtual_hair else
                'skin' if polygon.material_index in skin_indices else None)
        if kind == 'hair':
            hair_groups.update(g)
        for a, b in zip(g, g[1:] + g[:1]):
            if a != b:
                adjacency[a].add(b); adjacency[b].add(a)
                if kind is not None:
                    edges[tuple(sorted((a, b)))].add(kind)
    boundary_graph = defaultdict(set)
    for (a, b), kinds in edges.items():
        if len(kinds) == 2:
            boundary_graph[a].add(b); boundary_graph[b].add(a)
    remaining, components = set(boundary_graph), []
    while remaining:
        seed = remaining.pop()
        component, stack = {seed}, [seed]
        while stack:
            for vertex in boundary_graph[stack.pop()]:
                if vertex in remaining:
                    remaining.remove(vertex); component.add(vertex); stack.append(vertex)
        components.append(component)
    outer = max(components, key=len)
    assert len(outer) > 100
    seed = max(hair_groups - outer, key=lambda g: group_xyz[g, 2])
    interior, stack = {seed}, [seed]
    while stack:
        for vertex in adjacency[stack.pop()]:
            if vertex not in outer and vertex not in interior:
                interior.add(vertex); stack.append(vertex)
    # A broken perimeter would flood the face. Reject it before any mutation.
    assert .90 * len(hair_groups) < len(interior) < 1.10 * len(hair_groups)
    assert group_xyz[list(interior), 2].min() > 1.565
    moving = np.array(sorted(interior), dtype=np.int32)
    src = np.array([g for g in moving for _ in adjacency[g]], dtype=np.int32)
    dst = np.array([n for g in moving for n in sorted(adjacency[g])], dtype=np.int32)
    degree = np.bincount(src, minlength=len(group_xyz)).clip(1)
    smooth = group_xyz.copy()
    for _ in range(120):
        average = np.stack([np.bincount(src, weights=smooth[dst, a], minlength=len(smooth))
                            / degree for a in range(3)], axis=1)
        smooth[moving] = .45 * smooth[moving] + .55 * average[moving]
    displacement = smooth - group_xyz
    length = np.linalg.norm(displacement, axis=1).clip(1e-12)
    displacement *= np.minimum(1., .007 / length)[:, None]
    delta = np.zeros_like(original)
    delta[ids] = displacement[groups]
    # Identical deltas preserve every expression delta and welded UV seam.
    for key in mesh.shape_keys.key_blocks:
        coordinates = np.empty_like(original)
        key.data.foreach_get('co', coordinates.ravel())
        key.data.foreach_set('co', (coordinates + delta).ravel())
    mesh.vertices.foreach_set('co', (original + delta).ravel())
    cap = interior | outer
    filled, cap_faces = 0, set()
    for polygon in head_faces:
        if set(face_groups[polygon.index]) <= cap:
            if polygon.material_index != hair_index and polygon.index not in nape_faces:
                filled += 1
            polygon.material_index = hair_index
            cap_faces.add(polygon.index)
    mesh.update()
    bpy.context.view_layer.update()
    uv = mesh.uv_layers['UVMap']
    mesh.calc_loop_triangles()
    head_face_ids = {p.index for p in head_faces}
    source = {
        'source': 'V556 current body scalp; connected posterior extension and fixed outer hairline',
        'vertices': {str(v): (original[v] + delta[v]).tolist() for v in ids},
        'faces': [{'id': triangle.polygon_index, 'v': list(triangle.vertices),
                   'normal': list(triangle.normal),
                   'uv': [list(uv.data[l].uv) for l in triangle.loops]}
                  for triangle in mesh.loop_triangles
                  if triangle.polygon_index in head_face_ids],
    }
    movement = np.linalg.norm(delta, axis=1)
    report = {'changed_vertices': int(np.count_nonzero(movement > 1e-7)),
              'maximum_movement_mm': float(movement.max() * 1000),
              'mean_cap_movement_mm': float(np.linalg.norm(displacement[moving], axis=1).mean() * 1000),
              'outer_boundary_groups': len(outer), 'interior_groups': len(interior),
              'filled_internal_skin_faces': filled, 'cap_faces': len(cap_faces),
              'posterior_extension_faces': len(nape_faces),
              'posterior_minimum_center_z': 1.575,
              'ear_envelope_excluded': True,
              'shape_keys_preserved': len(mesh.shape_keys.key_blocks),
              'root_and_collision_surface': 'same smoothed current body',
              'status': 'TRIAL_REQUIRES_VISUAL_REVIEW'}
    (Path(output) / 'scalp-surface-report.json').write_text(json.dumps(report, indent=2))
    return source, cap_faces, report
