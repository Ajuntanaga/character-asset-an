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


STAGE = ROOT / "production_v209_lookdev"
SOURCE = ROOT / "production_v208_rig" / "ant_performance_rig_v208.blend"
OUTPUT = STAGE / "ant_photoreal_lookdev_v209.blend"
VALIDATION = STAGE / "audit" / "v209_blender_validation.json"
RECEIPT = STAGE / "audit" / "v209_build_receipt.json"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def sheet(items: list[tuple[str, Path]], output: Path, title: str) -> Path:
    cell_w, cell_h, pad, title_h, label_h, columns = 500, 650, 18, 72, 42, 3
    rows = (len(items) + columns - 1) // columns
    canvas = Image.new("RGB", (columns * cell_w + (columns + 1) * pad, title_h + rows * (cell_h + label_h + pad) + pad), (17, 24, 32))
    draw = ImageDraw.Draw(canvas)
    draw.text((pad, 17), title, font=ImageFont.truetype(BOLD, 29), fill=(236, 240, 245))
    font = ImageFont.truetype(FONT, 19)
    for index, (label, path) in enumerate(items):
        with Image.open(path) as source:
            rendered = ImageOps.contain(source.convert("RGB"), (cell_w, cell_h), Image.Resampling.LANCZOS)
        col, row = index % columns, index // columns
        x, y = pad + col * (cell_w + pad), title_h + row * (cell_h + label_h + pad)
        draw.rounded_rectangle((x, y, x + cell_w, y + cell_h), radius=10, fill=(29, 38, 48))
        canvas.paste(rendered, (x + (cell_w - rendered.width) // 2, y + (cell_h - rendered.height) // 2))
        draw.text((x + 6, y + cell_h + 9), label, font=font, fill=(216, 226, 235))
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output, optimize=True)
    return output


def main() -> None:
    validation = json.loads(VALIDATION.read_text(encoding="utf-8"))
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    output_hash = sha256(OUTPUT)
    if validation.get("status") != "PASS" or validation.get("validated_output_sha256") != output_hash:
        raise RuntimeError("V209 validation is absent or stale")
    if receipt.get("output", {}).get("sha256") != output_hash:
        raise RuntimeError("V209 receipt is stale")
    render_dir = STAGE / "renders" / "hero"
    delivery = STAGE / "delivery"
    contact = sheet(
        [(name.replace("_", " "), render_dir / f"{name}.png") for name in ("front", "three_quarter", "profile", "hero", "fretting_macro", "picking_macro")],
        delivery / "v209_photoreal_lookdev_contact.png",
        "V209 physically based hero look development",
    )
    status = STAGE / "HEADLESS_BUILD_STATUS_V209.md"
    status.write_text(
        "# HEADLESS BUILD STATUS V209\n\n"
        "- Status: PASS — physically based integrated hero look-development checkpoint.\n"
        f"- Output SHA-256: `{output_hash}`\n"
        "- Continuous voxel-unioned fretting hand, picking hand, and sleeves replace visible segmented construction pieces.\n"
        "- Procedural PBR skin, woven charcoal fabric, trouser cloth, boot leather, and sole rubber; six denoised Cycles views.\n\n"
        "## Honest visual boundary\n\n"
        "V209 materially improves continuity and physical response but remains a stylized/procedural likeness rather than scan-grade photorealism. The supplied sheets remain the authority; a production sculpt/texture pass by a character artist would still be required for human-closeup realism.\n",
        encoding="utf-8",
    )
    artifacts = [RECEIPT, STAGE / "audit" / "v209_lookdev_audit.json", STAGE / "audit" / "v209_render_manifest.json", VALIDATION, *sorted(render_dir.glob("*.png")), contact, status]
    record = make_stage_record("V209", SOURCE, OUTPUT, artifacts, validation)
    record["checkpoint"] = "V209_PHOTOREAL_LOOKDEV"
    record["visual_review"] = {
        "status": "PASS_PHYSICALLY_BASED_WITH_SCAN_GRADE_BOUNDARY",
        "accepted": "continuous interaction surfaces, stable PBR response, integrated hero lighting and performance framing",
        "remaining": "scan-grade facial/hand sculpt, fine tailoring and texture painting if literal photographic realism is required",
    }
    errors = validate_stage_record(record, "V209")
    if errors:
        raise RuntimeError(f"V209 stage record invalid: {errors}")
    audit = STAGE / "audit" / "v209_lookdev_audit_final.json"
    write_json(audit, record)
    print(f"V209_FINALIZE_OK audit={audit.relative_to(ROOT)} sha256={sha256(audit)}")


if __name__ == "__main__":
    main()
