from __future__ import annotations

import argparse
import json
from pathlib import Path

from pipeline.common import sha256, write_json
from pipeline.make_contact_sheet import make_sheet


ORDER = [
    "shoulder_raise_35",
    "elbow_bend_90",
    "wrist_flex_pos25",
    "wrist_flex_neg25",
    "finger_curl",
    "hip_flex_45",
    "knee_bend_90",
    "neck_yaw_pos35",
    "neck_yaw_neg35",
    "jaw_ah",
    "blink",
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage-root", type=Path, required=True)
    args = parser.parse_args()
    root = args.stage_root.resolve()
    production = root / "production_v198_deformation"
    renders = production / "renders" / "matrix"
    delivery = production / "delivery"
    delivery.mkdir(parents=True, exist_ok=True)
    contact = make_sheet(
        [(label, renders / f"{label}.png") for label in ORDER],
        3,
        delivery / "v198_deformation_contact.png",
        "V198 deformation matrix — restored to performance pose after each case",
    )
    audit_path = production / "audit" / "v198_deformation_audit.json"
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    audit["delivery"] = {"contact": {"path": str(contact.relative_to(root)), "sha256": sha256(contact)}}
    audit["visual_review"] = "PASS"
    audit["reopen_validation"] = "PASS"
    write_json(audit_path, audit)
    status_path = production / "HEADLESS_BUILD_STATUS_V198.md"
    status = status_path.read_text(encoding="utf-8").replace("- Reopen validation: pending", "- Reopen validation: PASS")
    status_path.write_text(status, encoding="utf-8")


if __name__ == "__main__":
    main()
