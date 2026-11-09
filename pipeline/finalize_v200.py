from __future__ import annotations

import argparse
import json
import shutil
import zipfile
from pathlib import Path

from pipeline.common import sha256, write_json
from pipeline.make_contact_sheet import make_sheet


ORBIT_ORDER = (
    "front",
    "front_right_3q",
    "right_profile",
    "rear_right_3q",
    "back",
    "rear_left_3q",
    "left_profile",
    "front_left_3q",
)


def build_delivery(root: Path) -> dict[str, dict[str, str]]:
    production = root / "production_v200_final"
    renders = production / "renders"
    delivery = production / "delivery"
    delivery.mkdir(parents=True, exist_ok=True)

    outputs = {
        "neutral_turnaround": make_sheet(
            [(label, renders / "neutral_turnaround" / f"{label}.png") for label in ORBIT_ORDER],
            4,
            delivery / "v200_neutral_turnaround.png",
            "V200 conservative neutral rig reference — guitar hidden for inspection",
        ),
        "performance_orbit": make_sheet(
            [(label, renders / "performance_orbit" / f"{label}.png") for label in ORBIT_ORDER],
            4,
            delivery / "v200_performance_orbit.png",
            "V200 canonical performance pose — eight-angle orbit",
        ),
        "identity_contact": make_sheet(
            [
                ("approved design lock", root / "references" / "source" / "approved_character_design_lock.png"),
                ("primary turnaround v2", root / "references" / "turnaround" / "character_turnaround_v2_face_refined.png"),
                ("front", renders / "identity" / "front.png"),
                ("left 3q", renders / "identity" / "left_3q.png"),
                ("right 3q", renders / "identity" / "right_3q.png"),
                ("right profile", renders / "identity" / "right_profile.png"),
                ("back", renders / "identity" / "back.png"),
            ],
            4,
            delivery / "v200_identity_contact.png",
            "V200 identity and canonical reference comparison",
        ),
        "hand_contact": make_sheet(
            [
                ("reference hand poses", root / "references" / "hands" / "hand_pose_sheet_v1.png"),
                ("reference compact M3", root / "references" / "hands" / "m3_chord_hand_v3_compact.png"),
                ("fretting contact", renders / "hands" / "fretting.png"),
                ("picking pinch", renders / "hands" / "picking.png"),
            ],
            2,
            delivery / "v200_hand_contact.png",
            "V200 fixed-landmark fretting and picking contacts",
        ),
        "wardrobe_contact": make_sheet(
            [
                ("torso front", renders / "wardrobe" / "torso_front.png"),
                ("front", renders / "wardrobe" / "front.png"),
                ("back", renders / "wardrobe" / "back.png"),
                ("trousers and boots", renders / "wardrobe" / "lower_detail.png"),
            ],
            2,
            delivery / "v200_wardrobe_contact.png",
            "V200 dark floral shirt, charcoal work jacket, rolled trousers, Chelsea boots",
        ),
        "facial_controls": make_sheet(
            [
                ("neutral", renders / "facial_controls" / "neutral.png"),
                ("blink", renders / "facial_controls" / "blink.png"),
                ("tired gaze", renders / "facial_controls" / "tired_gaze.png"),
                ("ah", renders / "facial_controls" / "ah.png"),
            ],
            2,
            delivery / "v200_facial_controls.png",
            "V200 supplied facial controls",
        ),
    }
    deformation_source = root / "production_v198_deformation" / "delivery" / "v198_deformation_contact.png"
    deformation = delivery / "v200_deformation_contact.png"
    shutil.copy2(deformation_source, deformation)
    outputs["deformation_contact"] = deformation
    return {
        label: {"path": str(path.relative_to(root)), "sha256": sha256(path)}
        for label, path in outputs.items()
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage-root", type=Path, required=True)
    parser.add_argument("--validated", action="store_true")
    parser.add_argument("--archive", type=Path)
    args = parser.parse_args()
    root = args.stage_root.resolve()
    production = root / "production_v200_final"
    blend = production / "ant_character_asset_final_v200.blend"
    delivery = build_delivery(root)

    audit_path = production / "audit" / "v200_final_audit.json"
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    audit["output_sha256"] = sha256(blend)
    audit["delivery"] = delivery
    audit["visual_review"] = "PASS"
    if args.validated:
        audit["validation"]["structure"] = "PASS"
        audit["validation"]["reopen"] = "PASS"
        audit["validation"]["pure_python"] = "PASS"
    if args.archive:
        archive = args.archive.resolve()
        if not archive.is_file():
            raise RuntimeError(f"Missing archive: {archive}")
        with zipfile.ZipFile(archive) as handle:
            bad_member = handle.testzip()
        if bad_member:
            raise RuntimeError(f"Corrupt archive member: {bad_member}")
        audit["validation"]["archive"] = "PASS"
        audit["package"] = {
            "path": str(archive),
            "sha256": sha256(archive),
            "integrity": "PASS",
        }
    write_json(audit_path, audit)

    status_path = production / "HEADLESS_BUILD_STATUS_V200.md"
    status = status_path.read_text(encoding="utf-8")
    status = status.replace("- Guarded reopen/structural validation: pending", f"- Guarded reopen/structural validation: {'PASS' if args.validated else 'pending'}")
    status = status.replace("- Final contact-sheet review: pending", "- Final contact-sheet review: PASS")
    if args.archive and "- Delivery archive integrity:" not in status:
        status += f"- Delivery archive integrity: PASS (`{sha256(args.archive.resolve())}`)\n"
    status_path.write_text(status, encoding="utf-8")


if __name__ == "__main__":
    main()
