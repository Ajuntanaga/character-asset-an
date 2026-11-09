"""Inspect weighted surface candidates for V248 fingertip contact solving."""

import json

import bpy


hand = bpy.data.objects["V248_FRETTING_HAND_REALISTIC"]
rig = bpy.data.objects["V239_CLEAN_CHARACTER_RIG"]
depsgraph = bpy.context.evaluated_depsgraph_get()
evaluated = hand.evaluated_get(depsgraph)
mesh = evaluated.to_mesh()
record = {
    "base_vertices": len(hand.data.vertices),
    "evaluated_vertices": len(mesh.vertices),
    "groups": {},
}
for digit in ("index", "middle", "ring", "pinky"):
    group_name = f"DEF-f_{digit}.03.L"
    group = hand.vertex_groups.get(group_name)
    candidates = []
    if group:
        for vertex in hand.data.vertices:
            try:
                weight = group.weight(vertex.index)
            except RuntimeError:
                continue
            if weight < 0.05:
                continue
            point = evaluated.matrix_world @ mesh.vertices[vertex.index].co
            candidates.append((weight, vertex.index, [round(float(v), 7) for v in point]))
    record["groups"][digit] = sorted(candidates, reverse=True)[:20]
group = hand.vertex_groups.get("DEF-thumb.03.L")
candidates = []
if group:
    for vertex in hand.data.vertices:
        try:
            weight = group.weight(vertex.index)
        except RuntimeError:
            continue
        if weight < 0.05:
            continue
        point = evaluated.matrix_world @ mesh.vertices[vertex.index].co
        candidates.append((weight, vertex.index, [round(float(v), 7) for v in point]))
record["groups"]["thumb"] = sorted(candidates, reverse=True)[:20]
evaluated.to_mesh_clear()
print("V248_FINGERTIPS=" + json.dumps(record, sort_keys=True))
