"""Tune only the ring-finger bend plane to clear the fretboard edge."""

from pathlib import Path
import importlib
import json
import sys

import bpy


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline import probe_v319_hybrid_fretting_matrix as pose
pose = importlib.reload(pose)
from pipeline import build_v320_collision_free_fretting as v320
v320 = importlib.reload(v320)


STAGE = ROOT / "production_v321_ring_clearance"
pose.RENDERS = STAGE / "renders" / "probe"
AUDIT = STAGE / "audit"
CANDIDATES = {
    "A_spread10": {"ring_spread": 10.0, "ring_curl": (14.0, 24.0, 14.0)},
    "B_spread12": {"ring_spread": 12.0, "ring_curl": (14.0, 24.0, 14.0)},
    "C_spread14": {"ring_spread": 14.0, "ring_curl": (14.0, 24.0, 14.0)},
    "D_spread12_curl28": {"ring_spread": 12.0, "ring_curl": (16.0, 28.0, 16.0)},
    "E_spread14_curl28": {"ring_spread": 14.0, "ring_curl": (16.0, 28.0, 16.0)},
    "F_spread16_curl30": {"ring_spread": 16.0, "ring_curl": (17.0, 30.0, 17.0)},
}


def main():
    pose.RENDERS.mkdir(parents=True, exist_ok=True)
    AUDIT.mkdir(parents=True, exist_ok=True)
    records = {}
    for label, tuning in CANDIDATES.items():
        settings = {
            "hand_delta": (-0.030, 0.025, 0.005),
            "hand_roll": 0.0,
            "guitar_yaw": -40.0,
            "guitar_delta": (-0.045, 0.005, 0.0),
            "curl": (14.0, 24.0, 14.0),
            "curl_by_digit": {"ring": tuning["ring_curl"]},
            "spread": 8.0,
            "spread_by_digit": {"ring": tuning["ring_spread"]},
        }
        record = pose.render_candidate(label, settings)
        rig = bpy.data.objects["V310_REOM_RIG"]
        root = bpy.data.objects["V206_GUITAR_ROOT"]
        collision = v320.collision_proxy(rig, root)
        ring_samples = [
            sample
            for bone in collision["digits"]["ring"]
            for sample in bone["samples"]
        ]
        record["collision_proxy_flag_count"] = collision["flagged_sample_count"]
        record["ring_min_lateral_clearance_m"] = min(sample["lateral_clearance_m"] for sample in ring_samples)
        record["ring_min_top_clearance_m"] = min(sample["top_clearance_m"] for sample in ring_samples)
        record["tuning"] = tuning
        records[label] = record
    output = {
        "schema": "v321-ring-clearance-probe-v1",
        "status": "VISUAL_AND_COLLISION_SELECTION_REQUIRED",
        "candidates": records,
    }
    (AUDIT / "v321_ring_clearance_probe.json").write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print("V321_RING_CLEARANCE_PROBE_OK=" + json.dumps({
        label: {
            "max_error_m": record["max_tip_target_error_m"],
            "collision_flags": record["collision_proxy_flag_count"],
        }
        for label, record in records.items()
    }, sort_keys=True))


if __name__ == "__main__":
    main()
