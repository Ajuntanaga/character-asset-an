"""Sweep millimeter-scale wrist offsets for zero proxy collision flags."""

from pathlib import Path
import importlib
import json
import sys

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline import probe_v319_hybrid_fretting_matrix as pose
pose = importlib.reload(pose)
from pipeline import build_v320_collision_free_fretting as v320
v320 = importlib.reload(v320)


SOURCE = ROOT / "production_v318_reference_guitar_rebuild" / "Character_An_reference_guitar_rebuild_v318.blend"
STAGE = ROOT / "production_v321_ring_clearance"
AUDIT = STAGE / "audit"
OUTPUT = AUDIT / "v321_lateral_clearance_sweep.json"
CASES = [
    (x, y)
    for x in (-0.045, -0.050, -0.055)
    for y in (0.005, 0.010, 0.015, 0.020, 0.025)
]


def main():
    AUDIT.mkdir(parents=True, exist_ok=True)
    records = []
    for longitudinal, lateral in CASES:
        bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
        pose.remove_charmorph_handlers()
        settings = {
            "hand_delta": (-0.030, 0.025, 0.005),
            "hand_roll": 0.0,
            "guitar_yaw": -40.0,
            "guitar_delta": (longitudinal, lateral, 0.0),
            "curl": (14.0, 24.0, 14.0),
            "spread": 8.0,
        }
        rig, targets = pose.pose_candidate(settings)
        root = bpy.data.objects["V206_GUITAR_ROOT"]
        collision = v320.collision_proxy(rig, root)
        errors = {}
        for digit, target in targets.items():
            tip = rig.matrix_world @ rig.pose.bones[f"DEF-f_{digit}.03.L"].tail
            errors[digit] = (tip - Vector(target["target_world_m"])).length
        inverse = root.matrix_world.inverted()
        bases = {
            digit: list(inverse @ (rig.matrix_world @ rig.pose.bones[f"DEF-f_{digit}.01.L"].head))
            for digit in targets
        }
        records.append({
            "guitar_delta_m": [longitudinal, lateral, 0.0],
            "max_tip_target_error_m": max(errors.values()),
            "tip_target_errors_m": errors,
            "collision_proxy_flags": collision["flagged_sample_count"],
            "flagged_samples": collision["flagged_samples"],
            "minimum_mcp_lateral_y_m": min(value[1] for value in bases.values()),
        })
    records.sort(key=lambda item: (item["collision_proxy_flags"], item["max_tip_target_error_m"], -item["minimum_mcp_lateral_y_m"]))
    result = {
        "schema": "v321-lateral-clearance-sweep-v1",
        "fixed_guitar_yaw_degrees": -40.0,
        "fretboard_half_width_near_contacts_m": 0.039,
        "cases": records,
        "selected": records[0],
    }
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("V321_LATERAL_CLEARANCE_SWEEP_OK=" + json.dumps({"selected": records[0], "zero_flag_cases": sum(item["collision_proxy_flags"] == 0 for item in records)}, sort_keys=True))


if __name__ == "__main__":
    main()
