"""Identify signed Rigify FK flexion axes for the V318 fretting wrist."""

from pathlib import Path
import json

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v318_reference_guitar_rebuild" / "Character_An_reference_guitar_rebuild_v318.blend"
STAGE = ROOT / "production_v319_fretting_hand"
AUDIT = STAGE / "audit"
OUTPUT = AUDIT / "v319_finger_seed_axes.json"
RIG = "V310_REOM_RIG"


def vec(value):
    return [round(float(component), 8) for component in value]


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    AUDIT.mkdir(parents=True, exist_ok=True)
    rig = bpy.data.objects[RIG]
    result = {}
    for digit in ("index", "middle", "ring", "pinky", "thumb"):
        ik_name = f"f_{digit}.01_ik.L" if digit != "thumb" else "thumb.01_ik.L"
        prefix = f"f_{digit}" if digit != "thumb" else "thumb"
        deform_prefix = f"DEF-f_{digit}" if digit != "thumb" else "DEF-thumb"
        deform_tip = rig.pose.bones[f"{deform_prefix}.03.L"]
        deform_base = rig.pose.bones[f"{deform_prefix}.01.L"]
        control = rig.pose.bones[ik_name]
        control["FK_IK"] = 0.0
        controls = [rig.pose.bones[f"{prefix}.{joint:02d}.L"] for joint in range(1, 4)]
        saved = {bone.name: bone.matrix_basis.copy() for bone in controls}

        def reset():
            for bone in controls:
                bone.matrix_basis = saved[bone.name].copy()
            bpy.context.view_layer.update()

        reset()
        base_world = rig.matrix_world @ deform_base.head
        neutral_tip = rig.matrix_world @ deform_tip.tail
        neutral_length = (neutral_tip - base_world).length
        probes = {}
        for bone in controls:
            probes[bone.name] = {}
            for axis, axis_name in enumerate("XYZ"):
                values = {}
                for angle in (-0.30, 0.30):
                    reset()
                    bone.rotation_mode = "XYZ"
                    bone.rotation_euler[axis] += angle
                    bpy.context.view_layer.update()
                    tip = rig.matrix_world @ deform_tip.tail
                    values[f"{angle:+.2f}"] = {
                        "tip_world_m": vec(tip),
                        "tip_delta_world_m": vec(tip - neutral_tip),
                        "base_tip_distance_m": round((tip - base_world).length, 8),
                        "distance_change_m": round((tip - base_world).length - neutral_length, 8),
                    }
                probes[bone.name][axis_name] = values
        reset()
        # The strongest negative distance change is the signed flexion probe.
        choices = []
        for bone_name, axes in probes.items():
            for axis_name, values in axes.items():
                for angle_label, value in values.items():
                    choices.append((value["distance_change_m"], bone_name, axis_name, float(angle_label)))
        choices.sort()
        result[digit] = {
            "base_world_m": vec(base_world),
            "neutral_tip_world_m": vec(neutral_tip),
            "neutral_base_tip_distance_m": round(neutral_length, 8),
            "strongest_flexion_probe": {
                "bone": choices[0][1],
                "axis": choices[0][2],
                "signed_angle_radians": choices[0][3],
                "distance_change_m": choices[0][0],
            },
            "probes": probes,
        }
    OUTPUT.write_text(json.dumps({"schema": "v319-finger-seed-axes-v1", "digits": result}, indent=2, sort_keys=True) + "\n")
    print("V319_FINGER_SEED_AXES_OK=" + str(OUTPUT))


if __name__ == "__main__":
    main()
