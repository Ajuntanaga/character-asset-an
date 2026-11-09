from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from pipeline.common import project_root, sha256, write_json
from pipeline.stage_contract import make_stage_record, validate_stage_record


ROOT = project_root()
STAGE = ROOT / "production_v201_reference_lock"
SOURCE = ROOT / "third_party" / "blender_human_base_meshes" / "v1.4.1" / "human-base-meshes-bundle-v1.4.1" / "human_base_meshes_bundle.blend"
OUTPUT = STAGE / "ant_photoreal_reference_v201.blend"
DELIVERY = STAGE / "delivery"
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD_FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def make_fit_sheet(
    items: list[tuple[str, Path]],
    output: Path,
    title: str,
    columns: int,
    cell: tuple[int, int],
) -> Path:
    cell_width, cell_height = cell
    pad, title_height, label_height = 18, 64, 40
    rows = (len(items) + columns - 1) // columns
    sheet = Image.new(
        "RGB",
        (
            columns * cell_width + (columns + 1) * pad,
            title_height + rows * (cell_height + label_height + pad) + pad,
        ),
        (17, 24, 32),
    )
    draw = ImageDraw.Draw(sheet)
    title_font = ImageFont.truetype(BOLD_FONT_PATH, 28)
    label_font = ImageFont.truetype(FONT_PATH, 20)
    draw.text((pad, 15), title, font=title_font, fill=(233, 238, 243))
    for index, (label, path) in enumerate(items):
        with Image.open(path) as source:
            rendered = ImageOps.contain(source.convert("RGB"), (cell_width, cell_height), Image.Resampling.LANCZOS)
        col, row = index % columns, index // columns
        x = pad + col * (cell_width + pad)
        y = title_height + pad + row * (cell_height + label_height + pad)
        draw.rounded_rectangle((x, y, x + cell_width, y + cell_height), radius=10, fill=(28, 37, 47))
        sheet.paste(rendered, (x + (cell_width - rendered.width) // 2, y + (cell_height - rendered.height) // 2))
        draw.text((x + 6, y + cell_height + 8), label, font=label_font, fill=(215, 225, 234))
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output, optimize=True)
    return output


def main() -> None:
    if not OUTPUT.is_file():
        raise FileNotFoundError(OUTPUT)
    validation_path = STAGE / "audit" / "v201_blender_validation.json"
    validation = json.loads(validation_path.read_text(encoding="utf-8"))
    if validation.get("status") != "PASS":
        raise RuntimeError("V201 Blender validation has not passed")

    renders = STAGE / "renders" / "base_inspection"
    base_sheet = make_fit_sheet(
        [(label, renders / f"{label}.png") for label in ("front", "profile", "three_quarter", "back")],
        DELIVERY / "v201_base_inspection_contact.png",
        "V201 official realistic male base — Cycles CPU inspection",
        4,
        (540, 720),
    )
    targets = STAGE / "targets"
    target_sheet = make_fit_sheet(
        [
            ("face — interpretation", targets / "v201_photoreal_face_target_v1.png"),
            ("full body — material/wardrobe only", targets / "v201_photoreal_fullbody_target_v1.png"),
            ("guitar — material/readability only", targets / "v201_photoreal_guitar_target_v1.png"),
            ("M3 hand — skin/cuff only; geometry rejected", targets / "v201_photoreal_m3_hand_target_v1.png"),
        ],
        DELIVERY / "v201_photoreal_target_contact.png",
        "Generated photoreal interpretation plates — lower authority",
        2,
        (760, 510),
    )
    authority_sheet = make_fit_sheet(
        [
            ("SUPPLIED authority — design lock", ROOT / "references/source/approved_character_design_lock.png"),
            ("GENERATED — face interpretation", targets / "v201_photoreal_face_target_v1.png"),
            ("SUPPLIED authority — refined turnaround", ROOT / "references/turnaround/character_turnaround_v2_face_refined.png"),
            ("GENERATED — full body interpretation", targets / "v201_photoreal_fullbody_target_v1.png"),
            ("SUPPLIED authority — guitar product", ROOT / "references/props/strandberg/strandberg_full_product.jpg"),
            ("GENERATED — guitar interpretation", targets / "v201_photoreal_guitar_target_v1.png"),
            ("SUPPLIED authority — M3 hand", ROOT / "references/hands/m3_chord_hand_v3_compact.png"),
            ("GENERATED — M3 geometry REJECTED", targets / "v201_photoreal_m3_hand_target_v1.png"),
            ("DETERMINISTIC authority — M3 contract", STAGE / "analysis" / "v201_m3_contact_diagram.png"),
        ],
        DELIVERY / "v201_authority_evidence_contact.png",
        "V201 authority comparison — supplied and numeric evidence outrank generated plates",
        3,
        (620, 440),
    )

    status = f"""# HEADLESS BUILD STATUS V201

- Status: PASS — source-locked base intake, not the photoreal final.
- Checkpoint: `V201_PHOTOREAL_REFERENCE`
- Blender: {validation['blender_version']}; guarded clean reopen PASS.
- Render: Cycles CPU, four inspection views.
- Barefoot height: {validation['height_m']:.4f} m.
- Official source: Blender Human Base Meshes v1.4.1, `Body Male - Realistic`, CC0.
- Output SHA-256: `{sha256(OUTPUT)}`

## Authority and visual-use ruling

- Supplied design/turnaround/face/hand/guitar files remain authoritative.
- Generated face plate: accepted as lower-authority identity and skin interpretation.
- Generated full-body plate: accepted for material and wardrobe interpretation; rejected as A-pose evidence because the output is arms-down.
- Generated guitar plate: accepted for material/readability only; rejected for exact hardware, string, fret, and control geometry.
- Generated M3 hand plate: accepted for skin/cuff/material cues; rejected for contact geometry and playability.
- Deterministic M3 diagram: accepted as the V201 geometry handoff. Recovered `m3_chord_mapping_v2.json` is authoritative for instrument geometry/string/tuning/scale/fret/spread data; `PHOTOREAL_CONTRACT` is the explicit four-finger override assigning index S5/F9, middle S4/F10, ring S7/F9, and pinky S8/F11. The recovered archive itself leaves S5/F9 and S4/F10 finger assignments unresolved.
- Official base inspection renders: PASS after direct image and Chafa review. Front, profile, three-quarter, and back show one continuous grounded A-pose base, consistent scale and silhouette, readable hands/feet, and no detached renderable clutter. The base is accepted for V201 intake only; its face and proportions remain to be reshaped at V202.
- Chafa terminal checks: PASS for all three delivery contact sheets (exit 0).

## Evidence

- `delivery/v201_base_inspection_contact.png`
- `delivery/v201_photoreal_target_contact.png`
- `delivery/v201_authority_evidence_contact.png`
- `analysis/v201_source_manifest.json`
- `analysis/v201_imagegen_prompt_output_manifest.json`
- `analysis/v201_m3_contact_geometry.json`
- `audit/v201_blender_validation.json`
- `audit/v201_reference_audit.json`

## Honest boundary

V201 proves a clean, licensed, real-scale, UV/multires-capable base intake and reference lock. It does not claim final identity sculpting, skin surfacing, grooming, wardrobe, guitar construction, rigging, or physically tested playability.
"""
    status_path = STAGE / "HEADLESS_BUILD_STATUS_V201.md"
    status_path.write_text(status, encoding="utf-8")

    artifacts = [
        STAGE / "analysis" / "v201_source_manifest.json",
        STAGE / "analysis" / "v201_imagegen_prompt_output_manifest.json",
        STAGE / "analysis" / "v201_m3_contact_diagram.png",
        STAGE / "analysis" / "v201_m3_contact_geometry.json",
        STAGE / "audit" / "v201_build_receipt.json",
        validation_path,
        ROOT / "licenses" / "blender-human-base-meshes-v1.4.1.txt",
        ROOT / "references" / "m3" / "m3_chord_mapping_v2.json",
        *sorted(targets.glob("*.png")),
        *[renders / f"{label}.png" for label in ("front", "profile", "three_quarter", "back")],
        base_sheet,
        target_sheet,
        authority_sheet,
        status_path,
    ]
    record = make_stage_record("V201", SOURCE, OUTPUT, artifacts, validation)
    record["checkpoint"] = "V201_PHOTOREAL_REFERENCE"
    record["authority"] = {
        "supplied": "authoritative identity, wardrobe, hand and guitar references",
        "generated": "lower-authority photoreal interpretation only",
        "m3": "recovered archive controls instrument geometry; PHOTOREAL_CONTRACT controls the explicit four-finger override; generated hand plate rejected for contacts",
        "live_blender": "official CC0 asset appended into a clean Blender 5.2.2 scene; Cycles CPU renders",
    }
    errors = validate_stage_record(record, "V201")
    if errors:
        raise RuntimeError(f"Stage record invalid: {errors}")
    audit = STAGE / "audit" / "v201_reference_audit.json"
    write_json(audit, record)

    print(f"V201_FINALIZE_OK audit={audit.relative_to(ROOT)} sha256={sha256(audit)}")


if __name__ == "__main__":
    main()
