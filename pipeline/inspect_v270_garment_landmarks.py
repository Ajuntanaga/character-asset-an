import json
import bpy

body = bpy.data.objects["V211_BODY_NEUTRAL"]
rig = bpy.data.objects["V239_CLEAN_CHARACTER_RIG"]
samples = {}
world = body.matrix_world
for z in (0.88, 0.96, 1.04, 1.12, 1.20, 1.28, 1.36, 1.44, 1.50):
    points = [world @ vertex.co for vertex in body.data.vertices if abs((world @ vertex.co).z - z) < 0.018]
    if points:
        samples[f"{z:.2f}"] = {
            "x": [round(min(p.x for p in points), 4), round(max(p.x for p in points), 4)],
            "y": [round(min(p.y for p in points), 4), round(max(p.y for p in points), 4)],
            "count": len(points),
        }

bones = {}
for name in (
    "spine_fk.001", "spine_fk.002", "spine_fk.003", "chest", "upper_arm_fk.L", "forearm_fk.L",
    "hand_fk.L", "upper_arm_fk.R", "forearm_fk.R", "hand_fk.R", "shoulder.L", "shoulder.R",
):
    bone = rig.pose.bones.get(name)
    if bone:
        bones[name] = {
            "head": [round(v, 4) for v in (rig.matrix_world @ bone.head)],
            "tail": [round(v, 4) for v in (rig.matrix_world @ bone.tail)],
        }

print("V270_GARMENT_LANDMARKS=" + json.dumps({"samples": samples, "bones": bones}, sort_keys=True))
