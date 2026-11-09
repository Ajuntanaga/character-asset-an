"""Measure Reom FK finger joint axes in the V310 guitar wrist pose."""

from pathlib import Path
import json

import bpy


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v310_reom_scene_alignment" / "Character_An_reom_scene_alignment_v310.blend"


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    rig = bpy.data.objects["V310_REOM_RIG"]
    result = {}
    for digit in ("index", "middle", "ring", "pinky", "thumb"):
        ik_name = f"f_{digit}.01_ik.L" if digit != "thumb" else "thumb.01_ik.L"
        prefix = f"f_{digit}" if digit != "thumb" else "thumb"
        deform = f"DEF-f_{digit}.03.L" if digit != "thumb" else "DEF-thumb.03.L"
        rig.pose.bones[ik_name]["FK_IK"] = 0.0
        controls = [rig.pose.bones[f"{prefix}.{joint:02d}.L"] for joint in range(1, 4)]
        saved = {bone.name: bone.matrix_basis.copy() for bone in controls}

        def reset():
            for bone in controls:
                bone.matrix_basis = saved[bone.name].copy()
            bpy.context.view_layer.update()

        reset()
        neutral = rig.matrix_world @ rig.pose.bones[deform].tail
        probes = {}
        for bone in controls:
            probes[bone.name] = {}
            for axis, axis_name in enumerate("XYZ"):
                values = {}
                for angle in (-0.25, 0.25):
                    reset()
                    bone.rotation_mode = "XYZ"
                    bone.rotation_euler[axis] += angle
                    bpy.context.view_layer.update()
                    tip = rig.matrix_world @ rig.pose.bones[deform].tail
                    values[f"{angle:+.2f}"] = {
                        "tip_world": list(tip),
                        "delta_world": list(tip - neutral),
                    }
                probes[bone.name][axis_name] = values
        reset()
        result[digit] = {"neutral_tip_world": list(neutral), "probes": probes}
    print("V310_FINGER_FK_AXES=" + json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
