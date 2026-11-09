"""Inspect dedicated V250 hand bone tips and surface landmarks in performance pose."""

import json

import bpy


armature = bpy.data.objects["V250_FRETTING_HAND_RIG"]
hand = bpy.data.objects["V248_FRETTING_HAND_REALISTIC"]
landmarks = {"index": 233, "middle": 213, "ring": 13, "pinky": 1, "thumb": 695}
depsgraph = bpy.context.evaluated_depsgraph_get()
evaluated = hand.evaluated_get(depsgraph)
mesh = evaluated.to_mesh()
record = {"bones": {}, "surface": {}, "evaluated_vertices": len(mesh.vertices)}
for digit in landmarks:
    bone = armature.pose.bones[f"{digit}_03"]
    record["bones"][digit] = [round(float(v), 7) for v in (armature.matrix_world @ bone.tail)]
    point = evaluated.matrix_world @ mesh.vertices[landmarks[digit]].co
    record["surface"][digit] = {"vertex": landmarks[digit], "world": [round(float(v), 7) for v in point]}
evaluated.to_mesh_clear()
print("V250_CONTACT_STATE=" + json.dumps(record, sort_keys=True))
