"""Report the neutral Reom fingertip/control constellation in the V310 pose."""

from pathlib import Path
import json

import bpy


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v310_reom_scene_alignment" / "Character_An_reom_scene_alignment_v310.blend"


def world_point(rig, point):
    return list(rig.matrix_world @ point)


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    rig = bpy.data.objects["V310_REOM_RIG"]
    records = {}
    for digit in ("index", "middle", "ring", "pinky", "thumb"):
        control_name = f"f_{digit}.01_ik.L" if digit != "thumb" else "thumb.01_ik.L"
        distal_name = f"DEF-f_{digit}.03.L" if digit != "thumb" else "DEF-thumb.03.L"
        control = rig.pose.bones[control_name]
        distal = rig.pose.bones[distal_name]
        records[digit] = {
            "control": control_name,
            "control_world_translation": list((rig.matrix_world @ control.matrix).translation),
            "control_parent": control.parent.name if control.parent else None,
            "control_props": {key: control[key] for key in control.keys() if isinstance(control[key], (int, float, bool, str))},
            "distal_head_world": world_point(rig, distal.head),
            "distal_tail_world": world_point(rig, distal.tail),
        }
    hand = rig.pose.bones["hand_ik.L"]
    parent = rig.pose.bones.get("upper_arm_parent.L")
    record = {
        "hand_world_matrix": [list(row) for row in (rig.matrix_world @ hand.matrix)],
        "hand_head_world": world_point(rig, rig.pose.bones["DEF-hand.L"].head),
        "hand_tail_world": world_point(rig, rig.pose.bones["DEF-hand.L"].tail),
        "hand_props": {key: hand[key] for key in hand.keys() if isinstance(hand[key], (int, float, bool, str))},
        "arm_parent_props": {key: parent[key] for key in parent.keys() if isinstance(parent[key], (int, float, bool, str))} if parent else {},
        "digits": records,
    }
    print("V310_FINGER_ALIGNMENT=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
