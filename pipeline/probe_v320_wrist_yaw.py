"""Probe guitar-space wrist yaw to move the knuckle row outside the neck."""

from pathlib import Path
import importlib
import json
import sys

import bpy


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline import probe_v319_hybrid_fretting_matrix as probe
probe = importlib.reload(probe)


STAGE = ROOT / "production_v320_collision_free_fretting"
probe.RENDERS = STAGE / "renders" / "yaw_probe"
AUDIT = STAGE / "audit"
CANDIDATES = {
    "K_yaw_neg20": (-20.0, 0.000),
    "L_yaw_neg30": (-30.0, 0.000),
    "M_yaw_neg40": (-40.0, 0.000),
    "N_yaw_neg50": (-50.0, 0.000),
    "O_yaw_neg35_y20": (-35.0, 0.020),
    "P_yaw_neg35_y40": (-35.0, 0.040),
}


def base_positions_local():
    rig = bpy.data.objects["V310_REOM_RIG"]
    root = bpy.data.objects["V206_GUITAR_ROOT"]
    inverse = root.matrix_world.inverted()
    result = {}
    for digit in ("index", "middle", "ring", "pinky"):
        bone = rig.pose.bones[f"DEF-f_{digit}.01.L"]
        result[digit] = list(inverse @ (rig.matrix_world @ bone.head))
    return result


def main():
    probe.RENDERS.mkdir(parents=True, exist_ok=True)
    AUDIT.mkdir(parents=True, exist_ok=True)
    records = {}
    for label, (yaw, lateral) in CANDIDATES.items():
        settings = {
            "hand_delta": (-0.030, 0.025, 0.005),
            "hand_roll": 0.0,
            "guitar_yaw": yaw,
            "guitar_delta": (0.0, lateral, 0.0),
            "curl": (14.0, 24.0, 14.0),
            "spread": 8.0,
        }
        record = probe.render_candidate(label, settings)
        bases = base_positions_local()
        record["mcp_bases_guitar_local_m"] = bases
        record["minimum_mcp_lateral_y_m"] = min(value[1] for value in bases.values())
        records[label] = record
    output = {
        "schema": "v320-wrist-yaw-probe-v1",
        "status": "VISUAL_AND_CLEARANCE_SELECTION_REQUIRED",
        "fretboard_half_width_near_contacts_m": 0.039,
        "candidates": records,
    }
    (AUDIT / "v320_wrist_yaw_probe.json").write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print("V320_WRIST_YAW_PROBE_OK=" + json.dumps({
        label: {"max_error_m": record["max_tip_target_error_m"], "minimum_mcp_y_m": record["minimum_mcp_lateral_y_m"]}
        for label, record in records.items()
    }, sort_keys=True))


if __name__ == "__main__":
    main()
