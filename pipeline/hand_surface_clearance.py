"""Evaluated inter-digit skin diagnostics and fit guidance; excludes shared webbing."""
import bpy
from mathutils.bvhtree import BVHTree


def compare_surfaces(vertices_a, faces_a, vertices_b, faces_b):
    """Triangle crossings plus sampled unsigned distance, not signed clearance."""
    a = BVHTree.FromPolygons(vertices_a, faces_a)
    b = BVHTree.FromPolygons(vertices_b, faces_b)
    distances = [target.find_nearest(point)[3]
                 for points, target in ((vertices_a, b), (vertices_b, a))
                 for point in points]
    crossings = a.overlap(b)
    return {'intersecting_face_pairs': len(crossings),
            'sampled_vertex_to_surface_min_m': min(distances),
            'sample_count': len(distances)}


def skin_surfaces(hand):
    evaluated = hand.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    try:
        digits = ('Index', 'Middle', 'Ring', 'Pinky')
        group_owner = {hand.vertex_groups[f'DEF-Finger_{digit}{j}.R'].index: digit
                       for digit in digits for j in (1, 2, 3)}
        owners = {}
        for v in mesh.vertices:
            weights = dict.fromkeys(digits, 0.)
            for g in v.groups:
                if g.group in group_owner:
                    weights[group_owner[g.group]] += g.weight
            owners[v.index] = next((d for d in digits if weights[d] > .95), None)
        surfaces = {}
        for digit in digits:
            polygons = [list(p.vertices) for p in mesh.polygons
                        if p.material_index == 0 and
                        all(owners[i] == digit for i in p.vertices)]
            assert polygons, f'Missing {digit} skin region'
            ids = sorted({i for face in polygons for i in face})
            index = {old: new for new, old in enumerate(ids)}
            surfaces[digit] = ([evaluated.matrix_world @ mesh.vertices[i].co for i in ids],
                               [[index[i] for i in face] for face in polygons])
        # World-space reflection reverses geometric face normals.
        if evaluated.matrix_world.to_3x3().determinant() < 0:
            surfaces = {d: (v, [list(reversed(f)) for f in faces])
                        for d, (v, faces) in surfaces.items()}
        return surfaces
    finally:
        evaluated.to_mesh_clear()


def measure(hand):
    surfaces = skin_surfaces(hand)
    digits = ('Index', 'Middle', 'Ring', 'Pinky')
    return {'method': 'evaluated skin, summed digit weights > .95; shared webbing and nails excluded',
            'limitations': 'Unsigned vertex sampling is not exact minimum or penetration depth; no crossing does not exclude containment or excluded-region collisions.',
            'pairs': {f'{a}-{b}': compare_surfaces(*surfaces[a], *surfaces[b])
                      for a, b in zip(digits, digits[1:])}}


def repulsion(hand, margin=.0006, samples_per_digit=128):
    """Local normal-distance penalty; open skin patches are not solid volumes.

    This guides optimization only. Full-resolution triangle crossings and visual
    inspection remain necessary; nearest-normal signs alone cannot certify fit.
    """
    surfaces = skin_surfaces(hand)
    trees = {d: BVHTree.FromPolygons(*surface) for d, surface in surfaces.items()}
    residual = []
    digits = ('Index', 'Middle', 'Ring', 'Pinky')
    for a, b in zip(digits, digits[1:]):
        for source, target in ((a, b), (b, a)):
            vertices = surfaces[source][0]
            count = min(samples_per_digit, len(vertices))
            weight = (8. / count) ** .5
            for k in range(count):
                point = vertices[k * len(vertices) // count]
                near, normal, _, distance = trees[target].find_nearest(point)
                # Remote open-patch backsides must not attract distant fingers.
                signed = (point - near).dot(normal)
                taper = max(0., min(1., (.015 - distance) / .005))
                residual.append(min(0., signed - margin) * weight * taper)
    return residual
