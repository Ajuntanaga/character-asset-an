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


STAGE = ROOT / "production_v205_wardrobe"
SOURCE = ROOT / "production_v204_groom" / "ant_groomed_character_v204.blend"
OUTPUT = STAGE / "ant_wardrobe_boots_v205.blend"
VALIDATION = STAGE / "audit" / "v205_blender_validation.json"
RECEIPT = STAGE / "audit" / "v205_build_receipt.json"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def sheet(items: list[tuple[str, Path]], output: Path, title: str, columns: int = 3) -> Path:
    cell_w, cell_h, pad, title_h, label_h = 520, 600, 18, 72, 42
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
        raise RuntimeError("V205 validation is absent or stale")
    if receipt.get("output", {}).get("sha256") != output_hash:
        raise RuntimeError("V205 receipt is stale")
    render_dir = STAGE / "renders" / "wardrobe"
    delivery = STAGE / "delivery"
    contact = sheet(
        [(name.replace("_", " "), render_dir / f"{name}.png") for name in (
            "front", "three_quarter", "profile", "rear", "torso_detail", "boots_detail",
        )],
        delivery / "v205_wardrobe_contact.png",
        "V205 fitted wardrobe and Chelsea-boot foundation",
    )
    comparison = sheet(
        [
            ("SUPPLIED turnaround", ROOT / "references" / "turnaround" / "character_turnaround_v2_face_refined.png"),
            ("V205 front", render_dir / "front.png"),
            ("V205 three quarter", render_dir / "three_quarter.png"),
            ("V205 profile", render_dir / "profile.png"),
            ("V205 torso detail", render_dir / "torso_detail.png"),
            ("V205 boots detail", render_dir / "boots_detail.png"),
        ],
        delivery / "v205_photo_reference_comparison.png",
        "V205 supplied-reference comparison",
    )
    status = STAGE / "HEADLESS_BUILD_STATUS_V205.md"
    status.write_text(
        "# HEADLESS BUILD STATUS V205\n\n"
        "- Status: PASS — fitted wardrobe and Chelsea-boot construction foundation.\n"
        f"- Output SHA-256: `{output_hash}`\n"
        "- Six Cycles CPU acceptance views; fitted shells replace rejected visible blockouts.\n"
        "- Authority: supplied sheets > analytic M3 > generated guidance.\n\n"
        "## Boundary\n\n"
        "V205 locks garment domains and body fit. Final cloth wrinkles, floral specificity, boot sculpt refinement, and unified hero realism remain V209 responsibilities.\n",
        encoding="utf-8",
    )
    artifacts = [
        RECEIPT, STAGE / "audit" / "v205_wardrobe_audit.json",
        STAGE / "audit" / "v205_render_manifest.json",
        STAGE / "audit" / "v205_validator_red_against_v204.json", VALIDATION,
        *sorted(render_dir.glob("*.png")), contact, comparison, status,
    ]
    record = make_stage_record("V205", SOURCE, OUTPUT, artifacts, validation)
    record["checkpoint"] = "V205_WARDROBE_BOOTS"
    record["visual_review"] = {
        "status": "PASS_WITH_V209_REFINEMENT_BOUNDARY",
        "accepted": "continuous fitted garment shells, open jacket lock, seven-button shirt, tapered rolled trousers, enclosed Chelsea boots",
        "remaining": "final wrinkle sculpture, exact floral print, and hero boot proportions",
    }
    errors = validate_stage_record(record, "V205")
    if errors:
        raise RuntimeError(f"V205 stage record invalid: {errors}")
    audit = STAGE / "audit" / "v205_wardrobe_audit_final.json"
    write_json(audit, record)
    print(f"V205_FINALIZE_OK audit={audit.relative_to(ROOT)} sha256={sha256(audit)}")


if __name__ == "__main__":
    main()
