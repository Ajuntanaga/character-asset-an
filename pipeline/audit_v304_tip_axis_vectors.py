from pathlib import Path
import json
import math

import bpy


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v304_fretting_rebind_probe" / "Character_An_fretting_rebind_probe_v304.blend"
OUTPUT = SOURCE.parent / "audit" / "v304_tip_axis_vectors.json"
PADS = {"index": 234, "middle": 211, "ring": 14, "pinky": 225, "thumb": 286}
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
hand = bpy.data.objects["V248_FRETTING_HAND_REALISTIC"]
rig = bpy.data.objects["V250_FRETTING_HAND_RIG"]
multires = next((modifier for modifier in hand.modifiers if modifier.type == "MULTIRES"), None)
if multires:
    multires.levels = 0
    multires.render_levels = 0


def reset_pose():
    for bone in rig.pose.bones:
        bone.location = (0, 0, 0)
        bone.rotation_mode = "XYZ"
        bone.rotation_euler = (0, 0, 0)
        bone.scale = (1, 1, 1)
    bpy.context.view_layer.update()


def point(index):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = hand.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    try:
        return rig.matrix_world.inverted() @ (evaluated.matrix_world @ mesh.vertices[index].co)
    finally:
        evaluated.to_mesh_clear()


result = {}
for digit, vertex in PADS.items():
    reset_pose()
    base = point(vertex)
    result[digit] = {"baseline_rig_local": list(base), "joint_01": {}}
    bone = rig.pose.bones[f"{digit}_01"]
    for axis, label in enumerate("xyz"):
        for sign in (-1, 1):
            reset_pose()
            bone.rotation_euler[axis] = sign * math.radians(28)
            bpy.context.view_layer.update()
            moved = point(vertex)
            result[digit]["joint_01"][f"{label}{sign:+d}"] = {
                "point_rig_local": list(moved),
                "delta_mm": list((moved - base) * 1000.0),
            }

record = {"schema": "v304-tip-axis-vectors-v1", "source": str(SOURCE.relative_to(ROOT)), "tips": result}
OUTPUT.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
print("V304_TIP_AXIS_VECTORS=" + json.dumps(record, sort_keys=True))
