from pathlib import Path
import json

import bpy

ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v300_guitar_visual_acceptance" / "Character_An_guitar_visual_acceptance_v300.blend"
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
hand = bpy.data.objects["V248_FRETTING_HAND_REALISTIC"]
rig = bpy.data.objects["V250_FRETTING_HAND_RIG"]

group_counts = {group.name: 0 for group in hand.vertex_groups}
for vertex in hand.data.vertices:
    for assignment in vertex.groups:
        group_counts[hand.vertex_groups[assignment.group].name] += 1

adjacency = [[] for _ in hand.data.vertices]
for edge in hand.data.edges:
    a, b = edge.vertices
    adjacency[a].append(b)
    adjacency[b].append(a)
components = []
unseen = set(range(len(adjacency)))
while unseen:
    seed = unseen.pop()
    stack = [seed]
    component = [seed]
    while stack:
        current = stack.pop()
        for neighbor in adjacency[current]:
            if neighbor in unseen:
                unseen.remove(neighbor)
                stack.append(neighbor)
                component.append(neighbor)
    components.append(component)

result = {
    "vertex_count": len(hand.data.vertices),
    "component_sizes": sorted((len(c) for c in components), reverse=True),
    "groups": group_counts,
    "bones": {
        bone.name: {"head": list(bone.head_local), "tail": list(bone.tail_local), "parent": bone.parent.name if bone.parent else None}
        for bone in rig.data.bones
    },
    "modifiers": [{"name": m.name, "type": m.type, "levels": getattr(m, "levels", None)} for m in hand.modifiers],
}
print("V300_FRETTING_BIND=" + json.dumps(result, sort_keys=True))
