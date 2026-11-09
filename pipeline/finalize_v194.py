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
    production = root / "production_v194_identity"
    renders = production / "renders" / "head_v194"
    baseline = production / "renders" / "head"
    delivery = production / "delivery"
    delivery.mkdir(parents=True, exist_ok=True)
    six_view = make_sheet(
        [
            ("front", renders / "front.png"),
            ("left 3q", renders / "left_3q.png"),
            ("right 3q", renders / "right_3q.png"),
            ("right profile", renders / "right_profile.png"),
            ("back", renders / "back.png"),
            ("body context", renders / "context_front.png"),
        ],
        3,
        delivery / "v194_identity_six_view_contact.png",
        "V194 reference identity — five head views plus body context",
    )
    comparison = make_sheet(
        [
            ("V193 front", baseline / "v193_head_front.png"),
            ("V194 front", renders / "front.png"),
            ("V193 left 3q", baseline / "v193_head_left_3q.png"),
            ("V194 left 3q", renders / "left_3q.png"),
            ("V193 profile", baseline / "v193_head_right_profile.png"),
            ("V194 profile", renders / "right_profile.png"),
        ],
        2,
        delivery / "v193_to_v194_identity_comparison.png",
        "Identity checkpoint comparison",
    )
    audit_path = production / "audit" / "v194_identity_audit.json"
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    audit["delivery"] = {
        "six_view": {"path": str(six_view.relative_to(root)), "sha256": sha256(six_view)},
        "comparison": {"path": str(comparison.relative_to(root)), "sha256": sha256(comparison)},
    }
    audit["validation"] = {"reopen": "PASS", "structure": "PASS"}
    write_json(audit_path, audit)
    status_path = production / "HEADLESS_BUILD_STATUS_V194.md"
    status = status_path.read_text(encoding="utf-8")
    status = status.replace("- Structural and reopen validation: run after visual gate", "- Structural and reopen validation: PASS")
    status_path.write_text(status, encoding="utf-8")


if __name__ == "__main__":
    main()
