"""Probe large wrist rolls to recover the dorsal fretting-hand presentation."""

from pathlib import Path
import json
import sys


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline import probe_v319_hybrid_fretting_matrix as probe


STAGE = ROOT / "production_v319_fretting_hand"
probe.RENDERS = STAGE / "renders" / "wrist_roll"
AUDIT = STAGE / "audit"
ROLLS = (-120.0, -90.0, -60.0, 60.0, 90.0, 120.0)


def main():
    probe.RENDERS.mkdir(parents=True, exist_ok=True)
    AUDIT.mkdir(parents=True, exist_ok=True)
    candidates = {}
    for roll in ROLLS:
        label = f"roll_{'neg' if roll < 0 else 'pos'}{abs(int(roll))}"
        settings = {
            "hand_delta": (-0.030, 0.025, 0.005),
            "hand_roll": roll,
            "curl": (14.0, 24.0, 14.0),
            "spread": 8.0,
        }
        candidates[label] = probe.render_candidate(label, settings)
    record = {
        "schema": "v319-large-wrist-roll-probe-v1",
        "status": "VISUAL_SELECTION_REQUIRED",
        "method": "Light FK curl seed plus large local-Y wrist roll",
        "candidates": candidates,
    }
    path = AUDIT / "v319_large_wrist_roll_probe.json"
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V319_LARGE_WRIST_ROLL_PROBE_OK=" + json.dumps({"candidates": list(candidates), "max_errors": {k: v["max_tip_target_error_m"] for k, v in candidates.items()}}, sort_keys=True))


if __name__ == "__main__":
    main()
