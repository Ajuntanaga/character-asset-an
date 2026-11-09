from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from PIL import Image

from pipeline.common import project_root, sha256, write_json
from pipeline.make_contact_sheet import make_sheet
from pipeline.reference_contract import REFERENCE_CONTRACT, validate_reference_contract


HEAD_LABELS = ("front", "left_3q", "right_3q", "right_profile", "back")
BODY_CAMERAS = {
    "front": "V151_FRONT_CAMERA",
    "front_right_3q": "V151_FRONT_RIGHT_3Q_CAMERA",
    "right_profile": "V151_RIGHT_PROFILE_CAMERA",
    "rear_right_3q": "V151_REAR_RIGHT_3Q_CAMERA",
    "back": "V151_BACK_CAMERA",
    "rear_left_3q": "V151_REAR_LEFT_3Q_CAMERA",
    "left_profile": "V151_LEFT_PROFILE_CAMERA",
    "front_left_3q": "V151_FRONT_LEFT_3Q_CAMERA",
}
HEAD_CAMERAS = {
    "front": "V95_CAM_HEAD_FRONT",
    "left_3q": "V95_CAM_HEAD_LEFT_THREEQUARTER",
    "right_3q": "V95_CAM_HEAD_RIGHT_THREEQUARTER",
    "right_profile": "V95_CAM_HEAD_RIGHT_PROFILE",
    "back": "V95_CAM_HEAD_BACK",
}


def parse_checksums(path: Path) -> dict[str, str]:
    checksums = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, relative = line.split(maxsplit=1)
        checksums[relative.strip()] = digest
    return checksums


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--head-source", type=Path, required=True)
    parser.add_argument("--v192", type=Path, required=True)
    parser.add_argument("--v193", type=Path, required=True)
    parser.add_argument("--body-contact", type=Path, required=True)
    args = parser.parse_args()

    root = project_root()
    errors = validate_reference_contract(root)
    if errors:
        raise SystemExit("reference contract failed: " + ", ".join(errors))

    output = root / "production_v194_identity"
    analysis = output / "analysis"
    head_output = output / "renders" / "head"
    delivery = output / "delivery"
    for directory in (analysis, head_output, delivery):
        directory.mkdir(parents=True, exist_ok=True)

    checksum_index = parse_checksums(root / "references" / "SHA256SUMS.txt")
    reference_records = []
    for item in REFERENCE_CONTRACT["authority"]:
        source = root / item["path"]
        archive_path = "/".join(Path(item["path"]).parts[1:])
        with Image.open(source) as image:
            dimensions = [image.width, image.height]
        actual = sha256(source)
        expected = checksum_index.get(archive_path)
        if actual != expected:
            raise SystemExit(f"checksum mismatch: {item['path']}")
        reference_records.append(
            {
                "id": item["id"],
                "path": item["path"],
                "archive_path": archive_path,
                "sha256": actual,
                "pixels": dimensions,
            }
        )

    write_json(
        analysis / "reference_measurements.json",
        {
            "schema": "character-reference-measurements-v1",
            "authority_order": [item["id"] for item in reference_records],
            "references": reference_records,
            "identity_locks": REFERENCE_CONTRACT["identity_locks"],
            "wardrobe_locks": REFERENCE_CONTRACT["wardrobe_locks"],
            "m3": REFERENCE_CONTRACT["m3"],
            "normalized_landmarks": REFERENCE_CONTRACT["normalized_landmarks"],
        },
    )

    head_renders = {}
    for label in HEAD_LABELS:
        source = args.head_source / f"v193_head_{label}.png"
        target = head_output / source.name
        shutil.copy2(source, target)
        head_renders[label] = {
            "camera": HEAD_CAMERAS[label],
            "path": str(target.relative_to(root)),
            "sha256": sha256(target),
        }
    head_contact = make_sheet(
        [(label, head_output / f"v193_head_{label}.png") for label in HEAD_LABELS],
        3,
        delivery / "v193_identity_baseline_contact.png",
        "V193 identity baseline — V95 head cameras",
    )

    body_render_records = {}
    for label, camera in BODY_CAMERAS.items():
        path = output / "renders" / "body" / f"v193_{label}.png"
        body_render_records[label] = {
            "camera": camera,
            "path": str(path.relative_to(root)),
            "sha256": sha256(path),
        }

    write_json(
        analysis / "v193_baseline_manifest.json",
        {
            "schema": "v193-baseline-manifest-v1",
            "runtime": "Blender 5.2.2 LTS",
            "source_v192": {"path": str(args.v192), "sha256": sha256(args.v192)},
            "source_v193": {"path": str(args.v193), "sha256": sha256(args.v193)},
            "head": head_renders,
            "body": body_render_records,
            "contacts": {
                "head": {"path": str(head_contact.relative_to(root)), "sha256": sha256(head_contact)},
                "body": {"path": str(args.body_contact), "sha256": sha256(args.body_contact)},
            },
            "note": "Body renders are the current V193 delivery orbit; head renders were produced from the same V193 checkpoint through the V95 camera group.",
        },
    )

    status = output / "STATUS_REFERENCE_LOCK.md"
    status.write_text(
        "# V194 Reference Lock\n\n"
        "Canonical authority order: approved design lock, v2 turnaround, v2 facial sheet, supplemental v3 turnaround, hand sheet, compact M3 hand.\n\n"
        "All extracted canonical files match the SHA-256 values embedded in `character_model_pack_v1.zip`. "
        "The identity baseline uses the five V95 head cameras; the body baseline uses the eight V151 orbit cameras.\n\n"
        f"- V192: `{sha256(args.v192)}`\n"
        f"- V193: `{sha256(args.v193)}`\n"
        "- Blender runtime: `5.2.2 LTS`\n"
        "- Measurements: `analysis/reference_measurements.json`\n"
        "- Baseline manifest: `analysis/v193_baseline_manifest.json`\n"
        "- Baseline contact: `delivery/v193_identity_baseline_contact.png`\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
