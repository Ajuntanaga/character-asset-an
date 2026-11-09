from pathlib import Path
import json
import math

import bpy


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v304_fretting_rebind_probe" / "Character_An_fretting_rebind_probe_v304.blend"
AUDIT = SOURCE.parent / "audit" / "v304_deformation_axes.json"
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
hand = bpy.data.objects["V248_FRETTING_HAND_REALISTIC"]
rig = bpy.data.objects["V250_FRETTING_HAND_RIG"]


def evaluated_points():
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = hand.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    try:
        return [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    finally:
        evaluated.to_mesh_clear()


def reset_pose():
    for pose_bone in rig.pose.bones:
        pose_bone.location = (0.0, 0.0, 0.0)
        pose_bone.rotation_mode = "XYZ"
        pose_bone.rotation_euler = (0.0, 0.0, 0.0)
        pose_bone.scale = (1.0, 1.0, 1.0)
    bpy.context.view_layer.update()


reset_pose()
baseline = evaluated_points()
probes = {}
for digit in ("index", "middle", "ring", "pinky", "thumb"):
    for joint in range(1, 4):
        name = f"{digit}_{joint:02d}"
        bone = rig.pose.bones[name]
        probes[name] = {}
        for axis, label in enumerate("xyz"):
            reset_pose()
            bone.rotation_euler[axis] = math.radians(28.0)
            bpy.context.view_layer.update()
            points = evaluated_points()
            displacements = [(current - base).length for current, base in zip(points, baseline)]
            probes[name][label] = {
                "mean_mm": 1000.0 * sum(displacements) / len(displacements),
                "max_mm": 1000.0 * max(displacements),
                "moved_vertices_over_0_5mm": sum(value > .0005 for value in displacements),
            }

result = {
    "schema": "v304-deformation-axes-v1",
    "source": str(SOURCE.relative_to(ROOT)),
    "modifier": [
        {
            "name": modifier.name,
            "type": modifier.type,
            "show_viewport": modifier.show_viewport,
            "show_render": modifier.show_render,
            "object": modifier.object.name if modifier.type == "ARMATURE" and modifier.object else None,
        }
        for modifier in hand.modifiers
    ],
    "bones": {
        bone.name: {
            "use_deform": bone.use_deform,
            "inherit_rotation": bone.use_inherit_rotation,
            "parent": bone.parent.name if bone.parent else None,
        }
        for bone in rig.data.bones
    },
    "probes": probes,
}
AUDIT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print("V304_DEFORMATION_AXES=" + json.dumps(result, sort_keys=True))
