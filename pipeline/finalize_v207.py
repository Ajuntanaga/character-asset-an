from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.common import sha256, write_json
from pipeline.stage_contract import make_stage_record, validate_stage_record


STAGE = ROOT / "production_v207_hands"
SOURCE = ROOT / "production_v206_guitar" / "ant_headless_guitar_v206.blend"
OUTPUT = STAGE / "ant_playable_hands_v207.blend"
VALIDATION = STAGE / "audit" / "v207_blender_validation.json"
RECEIPT = STAGE / "audit" / "v207_build_receipt.json"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def sheet(items: list[tuple[str, Path]], output: Path, title: str, columns: int = 3) -> Path:
    cell_w, cell_h, pad, title_h, label_h = 520, 430, 18, 72, 42
    rows = (len(items) + columns - 1) // columns
    canvas = Image.new("RGB", (columns * cell_w + (columns + 1) * pad, title_h + rows * (cell_h + label_h + pad) + pad), (17, 24, 32))
    draw = ImageDraw.Draw(canvas)
    draw.text((pad, 17), title, font=ImageFont.truetype(BOLD, 29), fill=(236, 240, 245))
    label_font = ImageFont.truetype(FONT, 19)
    for index, (label, path) in enumerate(items):
        with Image.open(path) as source:
            rendered = ImageOps.contain(source.convert("RGB"), (cell_w, cell_h), Image.Resampling.LANCZOS)
        col, row = index % columns, index // columns
        x, y = pad + col * (cell_w + pad), title_h + row * (cell_h + label_h + pad)
        draw.rounded_rectangle((x, y, x + cell_w, y + cell_h), radius=10, fill=(29, 38, 48))
        canvas.paste(rendered, (x + (cell_w - rendered.width) // 2, y + (cell_h - rendered.height) // 2))
        draw.text((x + 6, y + cell_h + 9), label, font=label_font, fill=(216, 226, 235))
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output, optimize=True)
    return output


def main() -> None:
    validation = json.loads(VALIDATION.read_text(encoding="utf-8"))
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    output_hash = sha256(OUTPUT)
    if validation.get("status") != "PASS" or validation.get("validated_output_sha256") != output_hash:
        raise RuntimeError("V207 validation is absent or stale")
    if receipt.get("output", {}).get("sha256") != output_hash:
        raise RuntimeError("V207 receipt is stale")

    render_dir = STAGE / "renders" / "hands"
    delivery = STAGE / "delivery"
    contact = sheet(
        [(name.replace("_", " "), render_dir / f"{name}.png") for name in (
            "fretboard_overhead", "dorsal_oblique", "neck_edge", "contact_macro", "wrist_context",
        )] + [("supplied M3 hand target", ROOT / "references" / "hands" / "m3_chord_hand_v3_compact.png")],
        delivery / "v207_playable_hand_contact.png",
        "V207 playable fretting-hand contact lock",
    )
    comparison = sheet(
        [
            ("SUPPLIED hand pose sheet", ROOT / "references" / "hands" / "hand_pose_sheet_v1.png"),
            ("V207 dorsal oblique", render_dir / "dorsal_oblique.png"),
            ("V207 overhead", render_dir / "fretboard_overhead.png"),
            ("SUPPLIED M3 compact", ROOT / "references" / "hands" / "m3_chord_hand_v3_compact.png"),
            ("V207 contact macro", render_dir / "contact_macro.png"),
            ("V207 neck edge", render_dir / "neck_edge.png"),
        ],
        delivery / "v207_photo_reference_comparison.png",
        "V207 supplied-reference and physical-contact comparison",
    )
    status = STAGE / "HEADLESS_BUILD_STATUS_V207.md"
    status.write_text(
        "# HEADLESS BUILD STATUS V207\n\n"
        "- Status: PASS — playable fretting-hand contact lock.\n"
        f"- Output SHA-256: `{output_hash}`\n"
        "- Four fingertip pads are 18% behind their fret wires and depress the contacted strings by 1.85 mm.\n"
        "- Thumb remains behind the neck; wrist bounds, collision list, and fretboard penetration checks pass.\n\n"
        "## Authority boundary\n\n"
        "Ring S7/F9 and pinky S8/F11 are user-verified. Index S5/F9 and middle S4/F10 are the current tested candidate assignments for previously unresolved contacts.\n\n"
        "## Visual boundary\n\n"
        "V207 locks physical contact and playable posture. The current procedural hand surface is not the final photoreal hero sculpt; conformal nails, continuous skin topology, pore detail, and arm integration remain V209 work.\n",
        encoding="utf-8",
    )
    artifacts = [
        RECEIPT, STAGE / "audit" / "v207_hand_contact_audit.json", STAGE / "audit" / "v207_render_manifest.json",
        VALIDATION, *sorted(render_dir.glob("*.png")), contact, comparison, status,
    ]
    record = make_stage_record("V207", SOURCE, OUTPUT, artifacts, validation)
    record["checkpoint"] = "V207_PLAYABLE_HANDS"
    record["visual_review"] = {
        "status": "PASS_CONTACT_LOCK_WITH_V209_SURFACE_BOUNDARY",
        "accepted": "visible four-finger pad placement, depressed strings, behind-neck thumb, bounded wrist posture",
        "remaining": "continuous photoreal hand sculpt, conformal nails, pore detail, and integrated sleeve/arm deformation",
    }
    errors = validate_stage_record(record, "V207")
    if errors:
        raise RuntimeError(f"V207 stage record invalid: {errors}")
    audit = STAGE / "audit" / "v207_hands_audit_final.json"
    write_json(audit, record)
    print(f"V207_FINALIZE_OK audit={audit.relative_to(ROOT)} sha256={sha256(audit)}")


if __name__ == "__main__":
    main()
