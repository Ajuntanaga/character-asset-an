"""Optional left-cuff interior weight trial; retain both sewn boundaries."""
from collections import Counter
import json
import bpy


def build(out):
    obj = bpy.data.objects['V357_CUFF_PATCH.L']
    rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
    assert len(rig.animation_data.drivers) == 1957
    counts = Counter(tuple(sorted(edge)) for face in obj.data.polygons for edge in face.edge_keys)
    boundary = {v for edge, count in counts.items() if count == 1 for v in edge}
    if not boundary or any(count > 2 for count in counts.values()):
        raise RuntimeError('Unexpected left cuff topology')
    adjacent = [set() for _ in obj.data.vertices]
    rest = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
    for edge in obj.data.edges:
        a, b = edge.vertices
        adjacent[a].add(b)
        adjacent[b].add(a)
    original = [{g.group: g.weight for g in vertex.groups} for vertex in obj.data.vertices]
    weights = original
    groups = sorted({group for vertex in weights for group in vertex})
    for _ in range(4):
        updated = []
        for index, current in enumerate(weights):
            if index in boundary or not adjacent[index]:
                updated.append(current.copy())
                continue
            influence = {j: 1 / max((rest[j] - rest[index]).length, 1e-5) ** 2 for j in adjacent[index]}
            total = sum(influence.values())
            updated.append({g: .5 * current.get(g, 0) + .5 * sum(
                weights[j].get(g, 0) * influence[j] for j in adjacent[index]) / total for g in groups})
        weights = updated
    for index, values in enumerate(weights):
        if index in boundary:
            assert values == original[index]
            continue
        for group, weight in values.items():
            obj.vertex_groups[group].add([index], weight, 'REPLACE')
    obj.data.update()
    bpy.context.view_layer.update()
    assert len(rig.animation_data.drivers) == 1957
    report = {'variant': 'distance-weighted', 'iterations': 4, 'object': obj.name,
              'fixed_boundary_vertices': len(boundary), 'vertices': len(weights),
              'main_drivers': 1957, 'quality_status': 'TRIAL_NOT_ACCEPTED'}
    (out / 'left-cuff-weight-report.json').write_text(json.dumps(report, indent=2))
    return report
