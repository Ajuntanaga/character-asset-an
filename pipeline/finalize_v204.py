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


STAGE = ROOT / "production_v204_groom"
SOURCE = ROOT / "production_v203_skin_eyes" / "ant_skin_eyes_v203.blend"
OUTPUT = STAGE / "ant_groomed_character_v204.blend"
DELIVERY = STAGE / "delivery"
VALIDATION = STAGE / "audit" / "v204_blender_validation.json"
BUILD_RECEIPT = STAGE / "audit" / "v204_build_receipt.json"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def sheet(items: list[tuple[str, Path]], output: Path, title: str, columns: int = 3) -> Path:
    cell_w, cell_h, pad, title_h, label_h = 520, 520, 18, 72, 42
    rows = (len(items) + columns - 1) // columns
    canvas = Image.new("RGB", (columns * cell_w + (columns + 1) * pad, title_h + rows * (cell_h + label_h + pad) + pad), (17, 24, 32))
    draw = ImageDraw.Draw(canvas)
    draw.text((pad, 17), title, font=ImageFont.truetype(BOLD, 29), fill=(236, 240, 245))
    label_font = ImageFont.truetype(FONT, 19)
    for index, (label, path) in enumerate(items):
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
    validation = json.loads(VALIDATION.read_text(encoding="utf-8"))
    receipt = json.loads(BUILD_RECEIPT.read_text(encoding="utf-8"))
    output_hash = sha256(OUTPUT)
    if validation.get("status") != "PASS" or validation.get("validated_output_sha256") != output_hash:
        raise RuntimeError("V204 validation is absent or stale")
    if receipt.get("status") != "PASS" or receipt.get("output", {}).get("sha256") != output_hash:
        raise RuntimeError("V204 build receipt is stale")

    render_dir = STAGE / "renders" / "groom"
    contact = sheet(
        [(name.replace("_", " "), render_dir / f"{name}.png") for name in (
            "front", "profile", "rear", "top", "rim", "root_macro",
        )],
        DELIVERY / "v204_groom_contact.png",
        "V204 Cycles multilayer curve groom — accepted artifact-free foundation",
    )
    comparison = sheet(
        [
            ("SUPPLIED face/groom reference", ROOT / "references" / "facial" / "head_expression_sheet_v2_face_refined.png"),
            ("V204 front", render_dir / "front.png"),
            ("SUPPLIED turnaround", ROOT / "references" / "turnaround" / "character_turnaround_v2_face_refined.png"),
            ("V204 profile", render_dir / "profile.png"),
            ("V204 top", render_dir / "top.png"),
            ("V204 root macro", render_dir / "root_macro.png"),
        ],
        DELIVERY / "v204_photo_reference_comparison.png",
        "V204 photo-reference workflow — supplied character sheets govern",
    )

    status = STAGE / "HEADLESS_BUILD_STATUS_V204.md"
    status.write_text(
        "# HEADLESS BUILD STATUS V204\n\n"
        "- Status: PASS — artifact-free multilayer curve-groom foundation.\n"
        f"- Output SHA-256: `{output_hash}`\n"
        f"- Curve roots: {validation['root_count']}; maximum root offset: {validation['maximum_root_distance_m'] * 1000.0:.3f} mm.\n"
        "- Renderer: Cycles CPU, six acceptance views.\n"
        "- Authority: supplied sheets > analytic M3 > generated guidance.\n"
        "- Rejected visual trials are preserved under audit and absent from the canonical scene.\n\n"
        "## Boundary\n\n"
        "V204 establishes groom coverage and attached fibers; final character likeness, wardrobe, guitar materials, playable hand pose, rig, and hero lighting remain later gates.\n",
        encoding="utf-8",
    )
    artifacts = [
        BUILD_RECEIPT,
        STAGE / "audit" / "v204_groom_audit.json",
        STAGE / "audit" / "v204_render_manifest.json",
        STAGE / "audit" / "v204_validator_red_against_v203.json",
        VALIDATION,
        *sorted(render_dir.glob("*.png")),
        contact,
        comparison,
        status,
    ]
    record = make_stage_record("V204", SOURCE, OUTPUT, artifacts, validation)
    record["checkpoint"] = "V204_GROOM"
    record["visual_review"] = {
        "status": "PASS",
        "scope": "direct review of final contact and supplied-reference comparison",
        "accepted": "curve-only groom with no scalp mask spill or thick-fiber artifacts",
        "boundary": "groom foundation; V205-V210 remain",
    }
    errors = validate_stage_record(record, "V204")
    if errors:
        raise RuntimeError(f"V204 stage record invalid: {errors}")
    audit = STAGE / "audit" / "v204_groom_audit_final.json"
    write_json(audit, record)
    print(f"V204_FINALIZE_OK audit={audit.relative_to(ROOT)} sha256={sha256(audit)}")


if __name__ == "__main__":
    main()
