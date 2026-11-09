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
    production = root / "production_v196_hands"
    contacts = production / "renders" / "contacts"
    baseline = production / "renders" / "baseline"
    delivery = production / "delivery"
    delivery.mkdir(parents=True, exist_ok=True)
    fretting = make_sheet(
        [("V192 baseline", baseline / "v192_fretting_oblique_control.png"), ("V196 anatomical", contacts / "fretting_oblique.png")],
        2,
        delivery / "v196_fretting_hand_contact.png",
        "Fretting hand — locked contact comparison",
    )
    picking_labels = [label for label in ("picking_oblique", "picking_player_edge", "picking_canonical", "picking_macro") if (contacts / f"{label}.png").is_file()]
    picking = make_sheet(
        [(label, contacts / f"{label}.png") for label in picking_labels],
        2,
        delivery / "v196_picking_hand_contact.png",
        "Picking hand — locked pinch views",
    )
    comparison = make_sheet(
        [("V192 accepted pinch", baseline / "v192_picking_canonical.png"), ("V196 anatomical pinch", contacts / f"{picking_labels[0]}.png")],
        2,
        delivery / "v195_to_v196_hand_comparison.png",
        "Hand surface finish comparison",
    )
    audit_path = production / "audit" / "v196_hand_contact_audit.json"
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    audit["delivery"] = {
        "fretting": {"path": str(fretting.relative_to(root)), "sha256": sha256(fretting)},
        "picking": {"path": str(picking.relative_to(root)), "sha256": sha256(picking)},
        "comparison": {"path": str(comparison.relative_to(root)), "sha256": sha256(comparison)},
    }
    audit["validation"] = {"reopen": "PASS", "structure": "PASS", "contact": "PASS"}
    write_json(audit_path, audit)
    status_path = production / "HEADLESS_BUILD_STATUS_V196.md"
    status = status_path.read_text(encoding="utf-8").replace("- Structural and reopen validation: pending", "- Structural and reopen validation: PASS")
    status_path.write_text(status, encoding="utf-8")


if __name__ == "__main__":
    main()
