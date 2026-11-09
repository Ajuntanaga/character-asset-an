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


STAGE = ROOT / "production_v203_skin_eyes"
SOURCE = ROOT / "production_v202_neutral_anatomy" / "ant_neutral_anatomy_v202.blend"
OUTPUT = STAGE / "ant_skin_eyes_v203.blend"
DELIVERY = STAGE / "delivery"
VALIDATION = STAGE / "audit" / "v203_blender_validation.json"
BUILD_RECEIPT = STAGE / "audit" / "v203_build_receipt.json"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def bound_validation() -> dict[str, object]:
    validation = json.loads(VALIDATION.read_text(encoding="utf-8"))
    receipt = json.loads(BUILD_RECEIPT.read_text(encoding="utf-8"))
    output_hash = sha256(OUTPUT)
    if validation.get("status") != "PASS" or validation.get("validated_output_sha256") != output_hash:
        raise RuntimeError("V203 validation is absent or stale")
    if validation.get("build_receipt_sha256") != sha256(BUILD_RECEIPT):
        raise RuntimeError("V203 validation is stale for the build receipt")
    if receipt.get("status") != "PASS" or receipt.get("output", {}).get("sha256") != output_hash:
        raise RuntimeError("V203 build receipt is stale")
    return validation


def sheet(items: list[tuple[str, Path]], output: Path, title: str, columns: int = 3) -> Path:
    cell_w, cell_h, pad, title_h, label_h = 520, 520, 18, 72, 42
    rows = (len(items) + columns - 1) // columns
    canvas = Image.new("RGB", (columns * cell_w + (columns + 1) * pad, title_h + rows * (cell_h + label_h + pad) + pad), (17, 24, 32))
    draw = ImageDraw.Draw(canvas)
    draw.text((pad, 17), title, font=ImageFont.truetype(BOLD, 29), fill=(236, 240, 245))
    label_font = ImageFont.truetype(FONT, 19)
    for index, (label, path) in enumerate(items):
        if not path.is_file():
            raise FileNotFoundError(path)
        with Image.open(path) as source:
            rendered = ImageOps.contain(source.convert("RGB"), (cell_w, cell_h), Image.Resampling.LANCZOS)
        col, row = index % columns, index // columns
        x = pad + col * (cell_w + pad)
        y = title_h + row * (cell_h + label_h + pad)
        draw.rounded_rectangle((x, y, x + cell_w, y + cell_h), radius=10, fill=(29, 38, 48))
        canvas.paste(rendered, (x + (cell_w - rendered.width) // 2, y + (cell_h - rendered.height) // 2))
        draw.text((x + 6, y + cell_h + 9), label, font=label_font, fill=(216, 226, 235))
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output, optimize=True)
    return output


def main() -> None:
    validation = bound_validation()
    render_dir = STAGE / "renders" / "lookdev"
    contact = sheet(
        [(name.replace("_", " "), render_dir / f"{name}.png") for name in (
            "face_neutral", "face_grazing", "eye", "lips", "ear",
            "hand_dorsal", "palm", "nails", "micro_undenoised",
        )],
        DELIVERY / "v203_skin_eye_contact.png",
        "V203 Cycles skin, eye, mouth, hand, and nail look development",
    )
    comparison = sheet(
        [
            ("SUPPLIED face sheet — highest authority", ROOT / "references" / "facial" / "head_expression_sheet_v2_face_refined.png"),
            ("V203 camera-matched neutral face", render_dir / "face_neutral.png"),
            ("GENERATED face guide — lower authority", ROOT / "production_v201_reference_lock" / "targets" / "v201_photoreal_face_target_v1.png"),
            ("V203 camera-matched grazing face", render_dir / "face_grazing.png"),
            ("GENERATED macro guide — lower authority", STAGE / "targets" / "v203_photoreal_macro_reference_v1.png"),
            ("V203 undenoised microdetail", render_dir / "micro_undenoised.png"),
        ],
        DELIVERY / "v203_photo_reference_comparison.png",
        "V203 photo-reference workflow — supplied sheets govern identity",
    )

    status = STAGE / "HEADLESS_BUILD_STATUS_V203.md"
    status.write_text(
        "# HEADLESS BUILD STATUS V203\n\n"
        "- Status: PASS — initial close-up skin, eye, oral, and nail look-development gate.\n"
        f"- Output SHA-256: `{sha256(OUTPUT)}`\n"
        f"- Texture tiles: {validation['texture_files']} project-relative 16-bit PNG files.\n"
        "- Renderer: Cycles CPU with adaptive sampling; one undenoised microdetail crop retained.\n"
        "- Authority: supplied sheets > analytic M3 > generated guidance.\n"
        "- Missing dependencies: 0.\n\n"
        "## Boundary\n\n"
        "V203 does not claim final groom, wardrobe, guitar, playable hand pose, rig, or hero lighting.\n",
        encoding="utf-8",
    )

    artifacts = [
        STAGE / "analysis" / "v203_texture_manifest.json",
        STAGE / "analysis" / "v203_photo_reference_manifest.json",
        BUILD_RECEIPT,
        STAGE / "audit" / "v203_render_manifest.json",
        STAGE / "audit" / "v203_validator_red_against_v202.json",
        VALIDATION,
        *sorted(render_dir.glob("*.png")),
        *sorted((STAGE / "textures").glob("*.png")),
        STAGE / "targets" / "v203_photoreal_macro_reference_v1.png",
        contact,
        comparison,
        status,
    ]
    record = make_stage_record("V203", SOURCE, OUTPUT, artifacts, validation)
    record["checkpoint"] = "V203_SKIN_EYES"
    record["visual_review"] = {
        "status": "PASS",
        "scope": "single direct review of V203 contact and reference-comparison sheets",
        "boundary": "initial surface look development; V204-V210 remain",
    }
    errors = validate_stage_record(record, "V203")
    if errors:
        raise RuntimeError(f"V203 stage record invalid: {errors}")
    audit = STAGE / "audit" / "v203_skin_eyes_audit.json"
    write_json(audit, record)
    print(f"V203_FINALIZE_OK audit={audit.relative_to(ROOT)} sha256={sha256(audit)}")


if __name__ == "__main__":
    main()
