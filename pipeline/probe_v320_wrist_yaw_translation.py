"""Pair guitar-space wrist yaw with longitudinal translation to retain reach."""

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
probe.RENDERS = STAGE / "renders" / "yaw_translation_probe"
AUDIT = STAGE / "audit"
CANDIDATES = {
    "Q_yaw30_x25_y20": (-30.0, -0.025, 0.020),
    "R_yaw35_x35_y10": (-35.0, -0.035, 0.010),
    "S_yaw40_x45_y05": (-40.0, -0.045, 0.005),
    "T_yaw40_x55_y00": (-40.0, -0.055, 0.000),
    "U_yaw45_x50_y00": (-45.0, -0.050, 0.000),
}


def base_positions_local():
    rig = bpy.data.objects["V310_REOM_RIG"]
    root = bpy.data.objects["V206_GUITAR_ROOT"]
    inverse = root.matrix_world.inverted()
    return {
        digit: list(inverse @ (rig.matrix_world @ rig.pose.bones[f"DEF-f_{digit}.01.L"].head))
        for digit in ("index", "middle", "ring", "pinky")
    }


def main():
    probe.RENDERS.mkdir(parents=True, exist_ok=True)
    AUDIT.mkdir(parents=True, exist_ok=True)
    records = {}
    for label, (yaw, longitudinal, lateral) in CANDIDATES.items():
        settings = {
            "hand_delta": (-0.030, 0.025, 0.005),
            "hand_roll": 0.0,
            "guitar_yaw": yaw,
            "guitar_delta": (longitudinal, lateral, 0.0),
            "curl": (14.0, 24.0, 14.0),
            "spread": 8.0,
        }
        record = probe.render_candidate(label, settings)
        bases = base_positions_local()
        record["mcp_bases_guitar_local_m"] = bases
        record["minimum_mcp_lateral_y_m"] = min(value[1] for value in bases.values())
        records[label] = record
    output = {
        "schema": "v320-wrist-yaw-translation-probe-v1",
        "status": "VISUAL_AND_CLEARANCE_SELECTION_REQUIRED",
        "fretboard_half_width_near_contacts_m": 0.039,
        "candidates": records,
    }
    (AUDIT / "v320_wrist_yaw_translation_probe.json").write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print("V320_WRIST_YAW_TRANSLATION_PROBE_OK=" + json.dumps({
        label: {"max_error_m": record["max_tip_target_error_m"], "minimum_mcp_y_m": record["minimum_mcp_lateral_y_m"]}
        for label, record in records.items()
    }, sort_keys=True))


if __name__ == "__main__":
    main()
