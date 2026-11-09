"""Move the FK-seeded fretting wrist toward the visible/dorsal reference side."""

from pathlib import Path
import json
import sys


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline import probe_v319_hybrid_fretting_matrix as probe


STAGE = ROOT / "production_v319_fretting_hand"
probe.RENDERS = STAGE / "renders" / "wrist_depth"
AUDIT = STAGE / "audit"
CANDIDATES = {
    "G_outward_20": {
        "hand_delta": (-0.032, 0.005, 0.006), "hand_roll": 0.0,
        "curl": (14.0, 24.0, 14.0), "spread": 8.0,
    },
    "H_outward_35": {
        "hand_delta": (-0.034, -0.010, 0.007), "hand_roll": 0.0,
        "curl": (14.0, 24.0, 14.0), "spread": 8.0,
    },
    "I_outward_35_roll5": {
        "hand_delta": (-0.034, -0.010, 0.007), "hand_roll": 5.0,
        "curl": (14.0, 24.0, 14.0), "spread": 8.0,
    },
    "J_outward_50": {
        "hand_delta": (-0.035, -0.025, 0.008), "hand_roll": 0.0,
        "curl": (14.0, 24.0, 14.0), "spread": 8.0,
    },
}


def main():
    probe.RENDERS.mkdir(parents=True, exist_ok=True)
    AUDIT.mkdir(parents=True, exist_ok=True)
    candidates = {label: probe.render_candidate(label, settings) for label, settings in CANDIDATES.items()}
    record = {
        "schema": "v319-wrist-depth-probe-v1",
        "status": "VISUAL_SELECTION_REQUIRED",
        "method": "Light FK curl seed with wrist translated outward along the guitar surface normal",
        "candidates": candidates,
    }
    path = AUDIT / "v319_wrist_depth_probe.json"
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V319_WRIST_DEPTH_PROBE_OK=" + json.dumps({"candidates": list(candidates), "max_errors": {k: v["max_tip_target_error_m"] for k, v in candidates.items()}}, sort_keys=True))


if __name__ == "__main__":
    main()
