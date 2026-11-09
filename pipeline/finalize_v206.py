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


STAGE = ROOT / "production_v206_guitar"
SOURCE = ROOT / "production_v205_wardrobe" / "ant_wardrobe_boots_v205.blend"
OUTPUT = STAGE / "ant_headless_guitar_v206.blend"
VALIDATION = STAGE / "audit" / "v206_blender_validation.json"
RECEIPT = STAGE / "audit" / "v206_build_receipt.json"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def sheet(items: list[tuple[str, Path]], output: Path, title: str, columns: int = 3) -> Path:
    cell_w, cell_h, pad, title_h, label_h = 520, 430, 18, 72, 42
    rows = (len(items) + columns - 1) // columns
    canvas = Image.new(
        "RGB",
        (columns * cell_w + (columns + 1) * pad, title_h + rows * (cell_h + label_h + pad) + pad),
        (17, 24, 32),
    )
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
        raise RuntimeError("V206 validation is absent or stale")
    if receipt.get("output", {}).get("sha256") != output_hash:
        raise RuntimeError("V206 receipt is stale")

    render_dir = STAGE / "renders" / "guitar"
    delivery = STAGE / "delivery"
    contact = sheet(
        [(name.replace("_", " "), render_dir / f"{name}.png") for name in (
            "front", "back", "beauty", "bridge_macro", "controls_macro", "fretboard_macro",
        )],
        delivery / "v206_guitar_contact.png",
        "V206 dimensionally authoritative eight-string headless guitar",
    )
    comparison = sheet(
        [
            ("SUPPLIED full product", ROOT / "references" / "props" / "strandberg" / "strandberg_full_product.jpg"),
            ("V206 front", render_dir / "front.png"),
            ("SUPPLIED user colorway", ROOT / "references" / "props" / "strandberg" / "user_colorway.png"),
            ("V206 beauty", render_dir / "beauty.png"),
            ("SUPPLIED controls", ROOT / "references" / "props" / "strandberg" / "strandberg_control_closeup.jpg"),
            ("V206 controls", render_dir / "controls_macro.png"),
        ],
        delivery / "v206_photo_reference_comparison.png",
        "V206 supplied-reference comparison",
    )
    status = STAGE / "HEADLESS_BUILD_STATUS_V206.md"
    status.write_text(
        "# HEADLESS BUILD STATUS V206\n\n"
        "- Status: PASS — dimensionally authoritative eight-string headless guitar.\n"
        f"- Output SHA-256: `{output_hash}`\n"
        "- 8 strings, 24 fanned frets, straight F7 neutral, 49 mm nut, 73.5 mm bridge.\n"
        "- Six isolated Cycles CPU acceptance views; corrected charcoal figured finish.\n\n"
        "## Boundary\n\n"
        "V206 locks the guitar geometry and materials. Performance hand contact is V207; unified hero realism remains V209.\n",
        encoding="utf-8",
    )
    artifacts = [
        RECEIPT,
        STAGE / "audit" / "v206_guitar_audit.json",
        STAGE / "audit" / "v206_render_manifest.json",
        STAGE / "audit" / "v206_validator_red_against_v205.json",
        VALIDATION,
        *sorted(render_dir.glob("*.png")),
        contact,
        comparison,
        status,
    ]
    record = make_stage_record("V206", SOURCE, OUTPUT, artifacts, validation)
    record["checkpoint"] = "V206_GUITAR"
    record["visual_review"] = {
        "status": "PASS",
        "accepted": "clean headless silhouette, fanned fretboard, eight physical strings, bridge tuners, pickups, controls, corrected charcoal figured finish",
        "remaining": "performance hand contact and final unified scene look development",
    }
    errors = validate_stage_record(record, "V206")
    if errors:
        raise RuntimeError(f"V206 stage record invalid: {errors}")
    audit = STAGE / "audit" / "v206_guitar_audit_final.json"
    write_json(audit, record)
    print(f"V206_FINALIZE_OK audit={audit.relative_to(ROOT)} sha256={sha256(audit)}")


if __name__ == "__main__":
    main()
