"""Measure V248 rest hand surface proximity to each V239 finger chain."""

import json

import bpy
from mathutils import Vector


hand = bpy.data.objects["V248_FRETTING_HAND_REALISTIC"]
rig = bpy.data.objects["V239_CLEAN_CHARACTER_RIG"]
previous = rig.data.pose_position
rig.data.pose_position = "REST"
bpy.context.view_layer.update()


def segment_distance(point: Vector, start: Vector, end: Vector) -> float:
    vector = end - start
    length = vector.length_squared
    if length <= 1e-12:
        return (point - start).length
    factor = max(0.0, min(1.0, (point - start).dot(vector) / length))
    return (point - (start + factor * vector)).length


chains = {}
for digit in ("index", "middle", "ring", "pinky"):
    names = [f"DEF-f_{digit}.0{joint}.L" for joint in range(1, 4)]
    chains[digit] = [
        (rig.matrix_world @ rig.data.bones[name].head_local, rig.matrix_world @ rig.data.bones[name].tail_local)
        for name in names
    ]
names = [f"DEF-thumb.0{joint}.L" for joint in range(1, 4)]
chains["thumb"] = [
    (rig.matrix_world @ rig.data.bones[name].head_local, rig.matrix_world @ rig.data.bones[name].tail_local)
    for name in names
]
points = [hand.matrix_world @ vertex.co for vertex in hand.data.vertices]
record = {
    "bounds": {
        "min": [round(min(point[i] for point in points), 6) for i in range(3)],
        "max": [round(max(point[i] for point in points), 6) for i in range(3)],
    },
    "chains": {},
    "nearest_chain_counts": {name: 0 for name in chains},
}
for name, segments in chains.items():
    distances = [min(segment_distance(point, *segment) for segment in segments) for point in points]
    closest = sorted(range(len(points)), key=lambda index: distances[index])[:12]
    record["chains"][name] = {
        "min_distance_m": round(min(distances), 6),
        "closest": [[index, round(distances[index], 6), [round(v, 6) for v in points[index]]] for index in closest],
    }
    distal_tail = segments[-1][1]
    tail_distances = [(point - distal_tail).length for point in points]
    tail_closest = sorted(range(len(points)), key=lambda index: tail_distances[index])[:16]
    record["chains"][name]["distal_tail"] = [round(v, 6) for v in distal_tail]
    record["chains"][name]["tail_closest"] = [
        [index, round(tail_distances[index], 6), [round(v, 6) for v in points[index]]]
        for index in tail_closest
    ]
for point in points:
    nearest = min(chains, key=lambda name: min(segment_distance(point, *segment) for segment in chains[name]))
    record["nearest_chain_counts"][nearest] += 1
rig.data.pose_position = previous
bpy.context.view_layer.update()
print("V248_BIND_FIT=" + json.dumps(record, sort_keys=True))
