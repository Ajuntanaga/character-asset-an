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
STAGE = ROOT / "production_v202_neutral_anatomy"
SOURCE = ROOT / "production_v201_reference_lock" / "ant_photoreal_reference_v201.blend"
OUTPUT = STAGE / "ant_neutral_anatomy_v202.blend"
DELIVERY = STAGE / "delivery"
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD_FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def load_bound_validation() -> dict[str, object]:
    validation_path = STAGE / "audit" / "v202_blender_validation.json"
    build_receipt_path = STAGE / "audit" / "v202_build_receipt.json"
    render_manifest_path = STAGE / "audit" / "v202_render_manifest.json"
    if not OUTPUT.is_file() or not validation_path.is_file() or not build_receipt_path.is_file():
        raise FileNotFoundError("V202 canonical output, validation, or build receipt missing")
    output_hash = sha256(OUTPUT)
    validation = json.loads(validation_path.read_text(encoding="utf-8"))
    receipt = json.loads(build_receipt_path.read_text(encoding="utf-8"))
    if validation.get("status") != "PASS":
        raise RuntimeError("V202 guarded Blender validation has not passed")
    if validation.get("validated_output_path") != str(OUTPUT.relative_to(ROOT)):
        raise RuntimeError("V202 validation is not bound to the canonical output path")
    if validation.get("validated_output_sha256") != output_hash:
        raise RuntimeError("V202 validation is stale for the canonical output hash")
    if validation.get("build_receipt_sha256") != sha256(build_receipt_path):
        raise RuntimeError("V202 validation is stale for the current build receipt")
    if receipt.get("status") != "PASS" or receipt.get("output", {}).get("sha256") != output_hash:
        raise RuntimeError("V202 build receipt is stale for the canonical output")
    if render_manifest_path.is_file():
        render_manifest = json.loads(render_manifest_path.read_text(encoding="utf-8"))
        if render_manifest.get("canonical_output") != {
            "path": str(OUTPUT.relative_to(ROOT)),
            "sha256": output_hash,
        }:
            raise RuntimeError("V202 render manifest is stale for the canonical output")
    return validation


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
        (columns * cell_width + (columns + 1) * pad, title_height + rows * (cell_height + label_height + pad) + pad),
        (17, 24, 32),
    )
    draw = ImageDraw.Draw(sheet)
    title_font = ImageFont.truetype(BOLD_FONT_PATH, 28)
    label_font = ImageFont.truetype(FONT_PATH, 20)
    draw.text((pad, 15), title, font=title_font, fill=(233, 238, 243))
    for index, (label, path) in enumerate(items):
        if not path.is_file():
            raise FileNotFoundError(path)
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


def make_scale_aligned_reference_sheet(output: Path) -> Path:
    """Build camera-matched pairs with fixed source crops and view labels."""
    face_sheet = ROOT / "references" / "facial" / "head_expression_sheet_v2_face_refined.png"
    turnaround = ROOT / "references" / "turnaround" / "character_turnaround_v2_face_refined.png"
    generated = ROOT / "production_v201_reference_lock" / "targets" / "v201_photoreal_face_target_v1.png"
    clay = STAGE / "renders" / "clay"
    pairs = [
        ("SUPPLIED FRONT — authority", face_sheet, (145, 5, 490, 520), "V202 CAMERA-LOCKED FRONT", clay / "head_front.png", (170, 60, 1430, 1580)),
        ("SUPPLIED 3/4 — authority", face_sheet, (585, 5, 1000, 520), "V202 CAMERA-LOCKED 3/4", clay / "head_three_quarter.png", (160, 60, 1440, 1580)),
        ("SUPPLIED PROFILE — authority", face_sheet, (1070, 5, 1480, 520), "V202 CAMERA-LOCKED PROFILE", clay / "head_profile.png", (150, 60, 1450, 1580)),
        ("SUPPLIED BODY FRONT — clothed silhouette authority", turnaround, (20, 20, 430, 1005), "V202 CAMERA-LOCKED BODY FRONT", clay / "body_front.png", (0, 0, 1200, 1600)),
        ("GENERATED FRONT — lower-authority guidance only", generated, (0, 0, 540, 724), "V202 CAMERA-LOCKED FRONT", clay / "head_front.png", (170, 60, 1430, 1580)),
    ]
    cell_width, cell_height = 520, 620
    pad, title_height, row_gap, label_height = 18, 74, 24, 34
    sheet = Image.new(
        "RGB",
        (2 * cell_width + 3 * pad, title_height + len(pairs) * (cell_height + label_height + row_gap) + pad),
        (17, 24, 32),
    )
    draw = ImageDraw.Draw(sheet)
    title_font = ImageFont.truetype(BOLD_FONT_PATH, 27)
    label_font = ImageFont.truetype(FONT_PATH, 18)
    draw.text((pad, 14), "V202 scale-aligned reference comparison — supplied sheets govern anatomy", font=title_font, fill=(233, 238, 243))
    for row, (left_label, left_path, left_crop, right_label, right_path, right_crop) in enumerate(pairs):
        with Image.open(left_path) as source:
            left = ImageOps.contain(source.convert("RGB").crop(left_crop), (cell_width, cell_height), Image.Resampling.LANCZOS)
        with Image.open(right_path) as source:
            right = ImageOps.contain(source.convert("RGB").crop(right_crop), (cell_width, cell_height), Image.Resampling.LANCZOS)
        y = title_height + row * (cell_height + label_height + row_gap)
        for col, (label, image) in enumerate(((left_label, left), (right_label, right))):
            x = pad + col * (cell_width + pad)
            sheet.paste(image, (x + (cell_width - image.width) // 2, y + (cell_height - image.height) // 2))
            draw.line((x, y + cell_height // 2, x + cell_width, y + cell_height // 2), fill=(90, 122, 145), width=1)
            draw.line((x + cell_width // 2, y, x + cell_width // 2, y + cell_height), fill=(90, 122, 145), width=1)
            draw.text((x + 4, y + cell_height + 7), label, font=label_font, fill=(215, 225, 234))
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output, optimize=True)
    return output


def main() -> None:
    if not OUTPUT.is_file():
        raise FileNotFoundError(OUTPUT)
    validation_path = STAGE / "audit" / "v202_blender_validation.json"
    validation = load_bound_validation()

    clay = STAGE / "renders" / "clay"
    wire = STAGE / "renders" / "wireframe"
    DELIVERY.mkdir(parents=True, exist_ok=True)
    body_sheet = make_fit_sheet(
        [
            ("front", clay / "body_front.png"),
            ("left three-quarter", clay / "body_three_quarter_l.png"),
            ("profile", clay / "body_profile.png"),
            ("right three-quarter", clay / "body_three_quarter_r.png"),
            ("back", clay / "body_back.png"),
        ],
        DELIVERY / "v202_clay_turnaround_contact.png",
        "V202 neutral anatomy — average-to-lean adult clay turnaround",
        5,
        (400, 600),
    )
    identity_sheet = make_fit_sheet(
        [
            ("SUPPLIED identity authority", ROOT / "references" / "source" / "approved_character_design_lock.png"),
            ("SUPPLIED face authority", ROOT / "references" / "facial" / "head_expression_sheet_v2_face_refined.png"),
            ("V202 clay front", clay / "head_front.png"),
            ("V202 clay three-quarter", clay / "head_three_quarter.png"),
            ("V202 clay profile", clay / "head_profile.png"),
        ],
        DELIVERY / "v202_identity_reference_comparison.png",
        "V202 identity comparison — supplied illustrations remain authoritative",
        5,
        (400, 520),
    )
    aligned_sheet = make_scale_aligned_reference_sheet(DELIVERY / "v202_scale_aligned_reference_comparison.png")
    macro_sheet = make_fit_sheet(
        [
            ("left hand", clay / "hand_left.png"),
            ("right hand", clay / "hand_right.png"),
            ("both hands", clay / "hands.png"),
            ("left foot", clay / "foot_left.png"),
            ("right foot", clay / "foot_right.png"),
            ("both feet", clay / "feet.png"),
        ],
        DELIVERY / "v202_anatomy_macro_contact.png",
        "V202 hand and foot anatomy — individual framing and distinct nail plates",
        3,
        (560, 620),
    )
    topology_sheet = make_fit_sheet(
        [("continuous production topology", wire / "topology_front.png")],
        DELIVERY / "v202_topology_evidence.png",
        "V202 topology evidence — helper anatomy hidden",
        1,
        (900, 1200),
    )
    mcp = STAGE / "audit" / "mcp"
    mcp_sheet = make_fit_sheet(
        [
            ("MCP curved eye caps — front", mcp / "head_front_curved_caps.png"),
            ("MCP curved eye caps — profile", mcp / "head_profile_curved_caps.png"),
            ("MCP surface-fit nails — left", mcp / "foot_left_raycast_nails_refined.png"),
            ("MCP surface-fit nails — right", mcp / "foot_right_raycast_nails_refined.png"),
        ],
        DELIVERY / "v202_mcp_correction_proof.png",
        "V202 interactive MCP correction proof persisted into deterministic builder",
        2,
        (760, 760),
    )

    status = f"""# HEADLESS BUILD STATUS V202

- Status: PASS — neutral anatomy and identity gate, not final skin or groom.
- Checkpoint: `V202_NEUTRAL_ANATOMY`
- Blender: {validation['blender_version']}; guarded clean reopen PASS.
- Render: Cycles CPU, 1600 px long-edge inspection views, AgX.
- Barefoot height: {validation['height_m']:.4f} m.
- Continuous body: {validation['body_connected_components']} component; {validation['body_vertices']} base vertices; UV and multires retained.
- Output SHA-256: `{sha256(OUTPUT)}`

## Corrective visual gate

- Adult identity silhouette: PASS for the V202 clay gate. The cranium is a slimmer compact oval, cheek breadth is retained while jaw/chin and neck taper, the alar base and sealed lips have more volume, and shoulder/torso/thigh mass is reduced toward the supplied average-to-lean silhouette.
- Eye anatomy: PASS for the clay gate. Iris/pupil surfaces are curved and dark; lid margins use the body clay material and the lacrimal anatomy is contained and subtle.
- Nostril depth: PASS. Both inserts validate posterior to the live alar surface.
- Hands and feet: PASS for neutral anatomy. Ten distinct hand nails and ten thin crowned toe plates occupy unique digit regions; every toe plate independently passes current evaluated-body closest-surface, ray-contact, and normal-alignment tolerances after clean reopen.
- Topology evidence: PASS. Helper anatomy is excluded from the wireframe render.
- Evidence binding: PASS. The validation, build receipt, render manifest, and finalizer all bind to the exact canonical V202 path and SHA-256; stale PASS records are rejected.
- Reference comparison: PASS. Camera-locked V202 renders are scale-aligned with supplied front/three-quarter/profile/body crops. The generated photoreal face plate is separately labeled lower-authority guidance.
- Supplied reference images remain authoritative; V202 is an anatomical translation, not a claim of exact real-person likeness.

## Evidence

- `delivery/v202_clay_turnaround_contact.png`
- `delivery/v202_identity_reference_comparison.png`
- `delivery/v202_scale_aligned_reference_comparison.png`
- `delivery/v202_anatomy_macro_contact.png`
- `delivery/v202_topology_evidence.png`
- `delivery/v202_mcp_correction_proof.png`
- `analysis/v202_landmark_measurements.json`
- `audit/v202_blender_validation.json`
- `audit/v202_render_manifest.json`

## Honest boundary

V202 establishes a continuous 1.80 m neutral production mesh, bounded adult identity/proportion shaping, production eye/oral/nail anatomy, and inspection cameras. Skin microstructure, final eye shaders, hair/beard, wardrobe, guitar, performance hand contacts, rigging, and hero lighting belong to later stages.
"""
    status_path = STAGE / "HEADLESS_BUILD_STATUS_V202.md"
    status_path.write_text(status, encoding="utf-8")

    artifacts = [
        STAGE / "analysis" / "v202_landmark_measurements.json",
        STAGE / "audit" / "v202_build_receipt.json",
        STAGE / "audit" / "v202_render_manifest.json",
        STAGE / "audit" / "v202_validator_red_against_v201.json",
        validation_path,
        *sorted(clay.glob("*.png")),
        *sorted(wire.glob("*.png")),
        body_sheet,
        identity_sheet,
        aligned_sheet,
        macro_sheet,
        topology_sheet,
        mcp_sheet,
        mcp / "head_front_curved_caps.png",
        mcp / "head_profile_curved_caps.png",
        mcp / "foot_left_raycast_nails_refined.png",
        mcp / "foot_right_raycast_nails_refined.png",
        mcp / "mcp_review_receipt.json",
        status_path,
    ]
    record = make_stage_record("V202", SOURCE, OUTPUT, artifacts, validation)
    record["checkpoint"] = "V202_NEUTRAL_ANATOMY"
    record["visual_review"] = {
        "status": "PASS",
        "scope": "one direct render review after corrective rebuild",
        "remaining_boundary": "neutral clay anatomy only; later-stage surfacing and performance are unclaimed",
    }
    errors = validate_stage_record(record, "V202")
    if errors:
        raise RuntimeError(f"Stage record invalid: {errors}")
    audit = STAGE / "audit" / "v202_neutral_anatomy_audit.json"
    write_json(audit, record)
    print(f"V202_FINALIZE_OK audit={audit.relative_to(ROOT)} sha256={sha256(audit)}")


if __name__ == "__main__":
    main()
