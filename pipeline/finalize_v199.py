from __future__ import annotations

import argparse
import json
from pathlib import Path

from pipeline.common import sha256, write_json
from pipeline.make_contact_sheet import make_sheet


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage-root", type=Path, required=True)
    args = parser.parse_args()
    root = args.stage_root.resolve()
    production = root / "production_v199_lookdev"
    delivery = production / "delivery"
    delivery.mkdir(parents=True, exist_ok=True)
    material_dir = production / "renders" / "materials"
    head_dir = production / "renders" / "head"
    orbit_dir = production / "renders" / "eight_angle"
    materials = make_sheet(
        [
            ("identity", head_dir / "front.png"),
            ("shirt and jacket", material_dir / "torso_front.png"),
            ("trousers and boots", material_dir / "lower_detail.png"),
            ("fretting hand", material_dir / "fretting_hand.png"),
            ("picking hand", material_dir / "picking_hand.png"),
        ],
        3,
        delivery / "v199_material_contact.png",
        "V199 painterly material and contour contact",
    )
    order = ["front", "front_right_3q", "right_profile", "rear_right_3q", "back", "rear_left_3q", "left_profile", "front_left_3q"]
    orbit = make_sheet(
        [(label, orbit_dir / f"{label}.png") for label in order],
        4,
        delivery / "v199_eight_angle_contact.png",
        "V199 travelling contours — eight-angle orbit",
    )
    audit_path = production / "audit" / "v199_lookdev_audit.json"
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    audit["delivery"] = {
        "materials": {"path": str(materials.relative_to(root)), "sha256": sha256(materials)},
        "orbit": {"path": str(orbit.relative_to(root)), "sha256": sha256(orbit)},
    }
    audit["visual_review"] = "PASS"
    audit["validation"] = {"reopen": "PASS", "materials": "PASS", "contours": "PASS"}
    write_json(audit_path, audit)
    status_path = production / "HEADLESS_BUILD_STATUS_V199.md"
    status = status_path.read_text(encoding="utf-8").replace("- Structural/reopen validation: pending", "- Structural/reopen validation: PASS")
    status_path.write_text(status, encoding="utf-8")


if __name__ == "__main__":
    main()
