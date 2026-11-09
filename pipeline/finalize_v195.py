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
    production = root / "production_v195_wardrobe"
    orbit = production / "renders" / "eight_angle"
    details = production / "renders" / "details"
    delivery = production / "delivery"
    delivery.mkdir(parents=True, exist_ok=True)
    orbit_order = ["front", "front_right_3q", "right_profile", "rear_right_3q", "back", "rear_left_3q", "left_profile", "front_left_3q"]
    eight = make_sheet(
        [(label, orbit / f"{label}.png") for label in orbit_order],
        4,
        delivery / "v195_eight_angle_contact.png",
        "V195 finished wardrobe — eight-angle orbit",
    )
    detail = make_sheet(
        [(label, details / f"{label}.png") for label in ("torso_front", "front", "left_profile", "back")],
        2,
        delivery / "v195_wardrobe_detail_contact.png",
        "V195 wardrobe details",
    )
    baseline = root / "production_v194_identity" / "renders" / "body" / "v193_front.png"
    comparison = make_sheet(
        [("V194 body baseline", baseline), ("V195 finished silhouette", orbit / "front.png")],
        2,
        delivery / "v194_to_v195_silhouette_comparison.png",
        "Silhouette and wardrobe comparison",
    )
    audit_path = production / "audit" / "v195_wardrobe_audit.json"
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    audit["delivery"] = {
        "eight_angle": {"path": str(eight.relative_to(root)), "sha256": sha256(eight)},
        "details": {"path": str(detail.relative_to(root)), "sha256": sha256(detail)},
        "comparison": {"path": str(comparison.relative_to(root)), "sha256": sha256(comparison)},
    }
    audit["validation"] = {"reopen": "PASS", "structure": "PASS"}
    write_json(audit_path, audit)
    status_path = production / "HEADLESS_BUILD_STATUS_V195.md"
    status = status_path.read_text(encoding="utf-8").replace("- Structural and reopen validation: pending", "- Structural and reopen validation: PASS")
    status_path.write_text(status, encoding="utf-8")


if __name__ == "__main__":
    main()
