from __future__ import annotations

import argparse
import json
import math
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from pipeline.common import project_root, sha256, write_json
from pipeline.photoreal_contract import PHOTOREAL_CONTRACT


ROOT = project_root()
STAGE = ROOT / "production_v201_reference_lock"
BUNDLE_ROOT = ROOT / "third_party" / "blender_human_base_meshes" / "v1.4.1"
BUNDLE = BUNDLE_ROOT / "human-base-meshes-bundle-v1.4.1.zip"
M3_JSON = ROOT / "references" / "m3" / "m3_chord_mapping_v2.json"
FONT = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
BOLD_FONT = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")

TARGETS = {
    "face": {
        "path": "production_v201_reference_lock/targets/v201_photoreal_face_target_v1.png",
        "sha256": "da0a068b6380d7def352fc96bc640a01496debc293488328c9fcb12de8c4a694",
        "accepted_for": ["identity translation", "skin and grooming material cues"],
        "rejected_for": [],
        "verbatim_prompt": (
            "Create a high-resolution, photorealistic studio head reference plate for a 3D character artist, faithfully translating the same adult male character shown in the attached supplied design sheets into believable real-world anatomy. Preserve identity: medium-brown skin; compact oval/rectangular face; broad cheek structure; moderately wide nose with natural alar shape; full lips held gently closed; dark brown eyes; heavy dark brows; dense short black curls with the visible part on the character's anatomical left; close trimmed full beard and a distinct narrow central gap in the mustache. Keep the same apparent age and proportions across every view. Layout: four large, non-overlapping orthographic-like views in a single row or clean 2x2 grid—front, anatomical-left three-quarter, anatomical-left profile, and rear/three-quarter hair view. Neutral relaxed expression, eyes level and looking straight relative to each view, head upright, no smile, no dramatic styling. 85–100 mm portrait lens feel, even cross-polarized-style studio illumination, neutral middle-gray background, realistic unretouched skin texture with pores and subtle asymmetry, sharp focus, no depth-of-field blur. Hairline, ears, nose, lips, eyelids, beard boundary, and mustache gap must be clearly readable. No clothing above a simple dark crew collar. No text, labels, measurement marks, logos, watermark, props, hands, guitar, duplicated facial features, fantasy elements, or painterly/cartoon rendering. This generated plate is an interpretation aid; prioritize strict consistency with the supplied sheets over beautification."
        ),
        "sources": [
            "references/source/approved_character_design_lock.png",
            "references/turnaround/character_turnaround_v2_face_refined.png",
            "references/facial/head_expression_sheet_v2_face_refined.png",
        ],
    },
    "full_body": {
        "path": "production_v201_reference_lock/targets/v201_photoreal_fullbody_target_v1.png",
        "sha256": "392469a6fb07f6b7e2c1dbcfc93812082db45e056102ace857c4209ec50759d3",
        "accepted_for": ["real-material interpretation", "wardrobe interpretation"],
        "rejected_for": ["production A-pose; generated plate is arms-down"],
        "verbatim_prompt": (
            "Create a high-resolution photorealistic full-body character turnaround plate for production 3D modeling, translating the exact same adult male character and outfit from the attached supplied sheets into a believable real person. Preserve identity and proportions from the supplied design: medium-brown skin, compact face, dense short black curls with the part on his anatomical left, trimmed beard/mustache; average-to-lean realistic adult build, approximately 1.80 m barefoot. Preserve wardrobe precisely: dark charcoal/black work jacket worn open with believable heavyweight fabric, construction seams and a left chest pen detail; dark floral button-up shirt underneath; black or deep-charcoal trousers with the same rolled cuffs; brown leather Chelsea boots with authentic panels, elastic gussets, welt, sole, creases, and wear. Layout four non-overlapping full-length views on one neutral-gray studio sheet: front, anatomical-left three-quarter, anatomical-left side, and back. Use the same neutral A-pose in all four views, arms angled about 35–45 degrees from torso, palms forward or slightly inward, feet shoulder-width and parallel, head level, neutral expression. Orthographic-like 70–100 mm lens feel, consistent scale and floor line, even color-neutral studio light, sharp focus from head to boots, physically plausible fabric folds, stitching, skin, hair, and leather. The jacket opening, underarm volume, cuffs, shirt hem, trouser rolls, and boot silhouette must be unambiguous. No guitar, no props, no text, labels, logos, watermark, dramatic pose, cropped limbs, overlapping views, extra fingers/limbs, or illustration/cartoon styling. Treat the supplied sheets as authoritative and do not redesign or beautify the character."
        ),
        "sources": [
            "references/source/approved_character_design_lock.png",
            "references/turnaround/character_turnaround_v2_face_refined.png",
            "references/turnaround/character_turnaround_supplemental_v3.png",
        ],
    },
    "guitar": {
        "path": "production_v201_reference_lock/targets/v201_photoreal_guitar_target_v1.png",
        "sha256": "ada91f8470603ca698867a9c624bcc123dd533e07d4195a2bad02ec38f684d72",
        "accepted_for": ["material response", "product-readability cues"],
        "rejected_for": ["exact hardware geometry", "string and fret geometry", "control placement authority"],
        "verbatim_prompt": (
            "Create a high-resolution photorealistic product-reference sheet for rebuilding the exact headless eight-string multiscale electric guitar shown in the attached supplied product and colorway references. Preserve the distinctive compact ergonomic double-cut body, headless neck, fanned 24 frets, zero fret/nut region, individual bridge/tuner hardware, pickup count and placement, control layout, jack placement, body bevels, contour cuts, strap buttons, and the supplied dark charcoal/black figured-wood colorway. The instrument must have exactly 8 separate strings from bridge to nut and physically plausible string gauges. Layout on a neutral middle-gray studio background: one large straight-on front view, one back view, one front three-quarter beauty view, plus three small orthographic closeups for bridge/tuners, controls, and neck/fretboard. Keep all views of the same exact instrument and scale. Use even color-neutral catalog lighting plus subtle grazing highlights so geometry, roughness, fingerprints, wood figure, metal brushing, screws, pickup pole pieces, fretwire, side dots, and finish boundaries are legible. Sharp focus, realistic materials, no hands or person, no stand, no text, labels, logos, watermark, cables, extra strings, conventional headstock, floating parts, fantasy hardware, or redesigned silhouette. The supplied references are authoritative; do not invent branding or change the colorway."
        ),
        "sources": [
            "references/props/strandberg/strandberg_full_product.jpg",
            "references/props/strandberg/strandberg_angle.jpg",
            "references/props/strandberg/strandberg_control_closeup.jpg",
            "references/props/strandberg/user_colorway.png",
        ],
    },
    "m3_hand": {
        "path": "production_v201_reference_lock/targets/v201_photoreal_m3_hand_target_v1.png",
        "sha256": "5b8b90764de9c4b5650e676ddfc4329d82853bda8ab7ab0b663cca3cada00f5f",
        "accepted_for": ["skin", "cuff", "material cues"],
        "rejected_for": ["contact geometry", "fingering", "playability evidence"],
        "verbatim_prompt": (
            "Create a high-resolution photorealistic macro reference plate for a 3D character artist showing the character's anatomical-left fretting hand gripping an eight-string headless multiscale electric-guitar neck around frets 7–12. Preserve the medium-brown skin, nail shape, hand proportions, and wrist/cuff language from the supplied character hand sheets. The neck must visibly and correctly have exactly 8 separate parallel fanned strings and clear metal frets. Use this fixed convention in the image: from the visual bottom edge of the fretboard to the visual top edge, strings are S1 through S8; S1 is low B and S8 is high A. Enforce these four fingertip-pad contacts exactly, immediately behind the named fret wire: index on S5 at fret 9, middle on S4 at fret 10, ring on S7 at fret 9, pinky on S8 at fret 11. The thumb stays behind the neck and does not cross the top edge. Show all four fretting digits clearly with believable joint bends, no collapsed knuckles, fingertip pads depressing strings, nails clear of the strings, and no neighboring-string collision. Keep a relaxed neutral wrist and realistic palm-to-neck clearance. Camera: player's/front three-quarter view close enough to count every string and fret, 85–120 mm macro lens feel, focus stacked, even neutral studio light, minimal reflections, physically believable skin, nail, metal, and dark figured wood. Include a small second inset from the side showing fingertip-pad depression and thumb placement, while preserving the same pose. No extra fingers, merged digits, missing strings, text, labels, logos, watermark, headstock, body, dramatic concert lighting, blur, or illustration style. The supplied geometry sheet is authoritative; photorealism must not change the contact assignment."
        ),
        "sources": [
            "references/hands/hand_pose_sheet_v1.png",
            "references/hands/m3_chord_hand_v3_compact.png",
            "references/props/strandberg/strandberg_full_product.jpg",
        ],
    },
}

SUPPLIED_EXTRA = [
    "references/props/strandberg/strandberg_full_product.jpg",
    "references/props/strandberg/strandberg_angle.jpg",
    "references/props/strandberg/strandberg_control_closeup.jpg",
    "references/props/strandberg/user_colorway.png",
]


def _image_record(path: Path) -> dict[str, Any]:
    with Image.open(path) as image:
        return {
            "path": str(path.relative_to(ROOT)),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
            "width": image.width,
            "height": image.height,
            "mode": image.mode,
        }


def _bundle_record() -> dict[str, Any]:
    if not BUNDLE.is_file():
        raise FileNotFoundError(BUNDLE)
    with zipfile.ZipFile(BUNDLE) as archive:
        members = [
            {"path": info.filename, "bytes": info.file_size, "crc32": f"{info.CRC:08x}"}
            for info in archive.infolist()
            if not info.is_dir()
        ]
    extracted_root = BUNDLE_ROOT / "human-base-meshes-bundle-v1.4.1"
    extracted_files = [
        {
            "path": str(path.relative_to(ROOT)),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        }
        for path in sorted(extracted_root.rglob("*"))
        if path.is_file()
    ]
    return {
        "url": PHOTOREAL_CONTRACT["official_base_url"],
        "retrieved_utc": datetime.fromtimestamp(BUNDLE.stat().st_mtime, timezone.utc).isoformat().replace("+00:00", "Z"),
        "path": str(BUNDLE.relative_to(ROOT)),
        "bytes": BUNDLE.stat().st_size,
        "sha256": sha256(BUNDLE),
        "license": "CC0 1.0",
        "license_record": "licenses/blender-human-base-meshes-v1.4.1.txt",
        "members": members,
        "extracted_files": extracted_files,
    }


def _fret_distance(scale_mm: float, fret: int) -> float:
    return scale_mm * (1.0 - 2.0 ** (-fret / 12.0))


def _string_y(string_index_low_to_high: int, x_mm: float, scale_mm: float) -> float:
    t = max(0.0, min(1.0, x_mm / scale_mm))
    low_to_high_fraction = string_index_low_to_high / 7.0
    nut_y = -24.5 + 49.0 * low_to_high_fraction
    bridge_y = -36.75 + 73.5 * low_to_high_fraction
    return nut_y + (bridge_y - nut_y) * t


def m3_provenance() -> dict[str, Any]:
    recovered = json.loads(M3_JSON.read_text(encoding="utf-8"))
    contract_m3 = PHOTOREAL_CONTRACT["m3"]
    geometry = recovered["instrument_geometry"]
    recovered_shared = {
        "string_order_low_to_high": [f"S{index}" for index in range(1, 9)],
        "tuning_low_to_high": recovered["coordinate_convention"]["tuning_low_to_high"],
        "scale_lengths_in_s8_to_s1": [geometry["scale_lengths_by_m3_string_in"][f"S{index}"] for index in range(8, 0, -1)],
        "frets": geometry["frets"],
        "neutral_fret": geometry["neutral_fret"],
        "nut_spread_mm": geometry["nut_string_spread_mm"],
        "bridge_spread_mm": geometry["bridge_string_spacing_mm"] * 7.0,
    }
    contract_shared = {key: contract_m3[key] for key in recovered_shared}
    if recovered_shared != contract_shared:
        raise RuntimeError(f"Recovered M3 geometry disagrees with approved contract: {recovered_shared} != {contract_shared}")
    recovered_notes = {
        f"{item['string']}/F{item['fret']}": {"finger": item["finger"], "status": item["status"]}
        for item in recovered["note_targets"]
    }
    if recovered_notes["S5/F9"]["finger"] is not None or recovered_notes["S4/F10"]["finger"] is not None:
        raise RuntimeError("Recovered archive unexpectedly claims the approved S5/F9 or S4/F10 finger override")
    return {
        "instrument_geometry_source": {
            "path": str(M3_JSON.relative_to(ROOT)),
            "sha256": sha256(M3_JSON),
            "authority": "recovered archive; authoritative for instrument geometry, string convention, tuning, scales, frets, neutral fret and spreads",
        },
        "finger_override_source": {
            "path": "pipeline/photoreal_contract.py",
            "sha256": sha256(ROOT / "pipeline" / "photoreal_contract.py"),
            "authority": "approved implementation contract; authoritative four-finger override",
        },
        "shared_geometry_cross_check": {"status": "PASS", "recovered": recovered_shared, "approved_contract": contract_shared},
        "recovered_note_targets": recovered_notes,
        "approved_four_finger_override": contract_m3["finger_targets"],
        "override_note": "The recovered archive leaves S5/F9 and S4/F10 fingering unresolved; it does not contain the approved index/middle assignments. PHOTOREAL_CONTRACT explicitly supplies index S5/F9 and middle S4/F10 while retaining ring S7/F9 and pinky S8/F11.",
    }


def make_m3_diagram(output: Path, geometry_output: Path) -> Path:
    m3 = PHOTOREAL_CONTRACT["m3"]
    provenance = m3_provenance()
    recovered_geometry = provenance["shared_geometry_cross_check"]["recovered"]
    scales_s8_to_s1 = recovered_geometry["scale_lengths_in_s8_to_s1"]
    scales = {f"S{8 - index}": inches * 25.4 for index, inches in enumerate(scales_s8_to_s1)}
    strings = list(recovered_geometry["string_order_low_to_high"])
    tuning = dict(zip(strings, recovered_geometry["tuning_low_to_high"]))
    fret_positions = {
        fret: {string: _fret_distance(scales[string], fret) for string in strings}
        for fret in range(7, 13)
    }
    all_x = [value for positions in fret_positions.values() for value in positions.values()]
    x_min, x_max = min(all_x) - 10.0, max(all_x) + 8.0

    width, height = 1800, 1040
    left, right, top, bottom = 150, 1360, 225, 845
    image = Image.new("RGB", (width, height), (17, 23, 31))
    draw = ImageDraw.Draw(image)
    title_font = ImageFont.truetype(str(BOLD_FONT), 34)
    body_font = ImageFont.truetype(str(FONT), 22)
    small_font = ImageFont.truetype(str(FONT), 18)
    label_font = ImageFont.truetype(str(BOLD_FONT), 20)

    def px(x_mm: float) -> float:
        return left + (x_mm - x_min) / (x_max - x_min) * (right - left)

    def py(y_mm: float) -> float:
        return bottom - (y_mm + 42.0) / 84.0 * (bottom - top)

    draw.text((60, 45), "Deterministic M3 contact geometry — authoritative numeric contract", font=title_font, fill=(235, 240, 245))
    draw.text((60, 103), "Instrument geometry: recovered archive · four-finger mapping: approved PHOTOREAL_CONTRACT override", font=body_font, fill=(174, 193, 211))
    draw.text((60, 138), "S1 bottom/low-B → S8 top/high-A · fan F7–F12 · pad centers 18% behind fret wire", font=small_font, fill=(145, 168, 188))

    # Frets are fan lines joining true per-string multiscale intersections.
    for fret in range(7, 13):
        points = []
        for index, string in enumerate(strings):
            x = fret_positions[fret][string]
            y = _string_y(index, x, scales[string])
            points.append((px(x), py(y)))
        color = (238, 188, 74) if fret == 7 else (148, 157, 166)
        draw.line(points, fill=color, width=5 if fret == 7 else 3)
        draw.text((points[-1][0] - 16, top - 43), f"F{fret}", font=label_font, fill=color)

    # Strings are drawn over the full visible fret window.
    for index, string in enumerate(strings):
        scale = scales[string]
        y0 = _string_y(index, x_min, scale)
        y1 = _string_y(index, x_max, scale)
        thickness = 2 + (7 - index) // 2
        draw.line((px(x_min), py(y0), px(x_max), py(y1)), fill=(205, 211, 218), width=thickness)
        draw.text((28, py(y0) - 14), f"{string}  {tuning[string]}", font=label_font, fill=(230, 235, 240))

    finger_colors = {
        "index": (75, 192, 255),
        "middle": (102, 222, 167),
        "ring": (255, 170, 73),
        "pinky": (226, 107, 220),
    }
    contacts = []
    for finger, (string, fret) in m3["finger_targets"].items():
        string_index = strings.index(string)
        wire_x = _fret_distance(scales[string], fret)
        prior_x = _fret_distance(scales[string], fret - 1)
        pad_x = wire_x - 0.18 * (wire_x - prior_x)
        pad_y = _string_y(string_index, pad_x, scales[string])
        point = (px(pad_x), py(pad_y))
        color = finger_colors[finger]
        draw.ellipse((point[0] - 18, point[1] - 18, point[0] + 18, point[1] + 18), fill=color, outline=(245, 249, 252), width=4)
        draw.text((point[0] + 22, point[1] - 16), f"{finger} {string}/F{fret}", font=label_font, fill=color)
        contacts.append(
            {
                "finger": finger,
                "string": string,
                "fret": fret,
                "scale_mm": round(scales[string], 3),
                "wire_x_from_nut_mm": round(wire_x, 3),
                "pad_x_from_nut_mm": round(pad_x, 3),
                "pad_y_mm": round(pad_y, 3),
                "pad_rule": "18_percent_of_prior_fret_space_toward_nut",
            }
        )

    panel_x = 1410
    draw.rounded_rectangle((panel_x, 175, 1750, 855), radius=18, fill=(28, 37, 47), outline=(69, 87, 103), width=2)
    draw.text((panel_x + 24, 205), "Contract", font=title_font, fill=(235, 240, 245))
    lines = [
        "24 frets",
        "F7 neutral",
        "nut spread 49.0 mm",
        "bridge spread 73.5 mm",
        "scales S8→S1:",
        "26.50, 26.71, 26.93,",
        "27.14, 27.36, 27.57,",
        "27.79, 28.00 inches",
        "",
        "THUMB RESTRICTION",
        "rear-neck support only",
        "hidden from fretboard view",
        "must not cross top edge",
        "",
        "Generated hand plate:",
        "REJECTED for geometry",
    ]
    y = 270
    for line in lines:
        color = (255, 170, 73) if "THUMB" in line or "REJECTED" in line else (203, 215, 225)
        draw.text((panel_x + 24, y), line, font=body_font if line else small_font, fill=color)
        y += 34 if line else 19

    draw.text((60, 915), "Geometric target only: supports later Blender-local contact solving; does not claim physical-instrument validation.", font=body_font, fill=(174, 193, 211))
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, optimize=True)
    write_json(
        geometry_output,
        {
            "schema": "v201-m3-contact-geometry-v1",
            "provenance": provenance,
            "string_convention": "S1 bottom/low-B through S8 top/high-A",
            "tuning_low_to_high": recovered_geometry["tuning_low_to_high"],
            "fret_window": [7, 12],
            "contacts": contacts,
            "thumb": {"role": "rear-neck support", "visible_from_fretboard_camera": False, "may_cross_top_edge": False},
        },
    )
    return output


def run() -> dict[str, Path]:
    analysis = STAGE / "analysis"
    analysis.mkdir(parents=True, exist_ok=True)
    supplied_paths = [ROOT / item["path"] for item in PHOTOREAL_CONTRACT["authority"]]
    supplied_paths.extend(ROOT / path for path in SUPPLIED_EXTRA)
    supplied = [_image_record(path) for path in supplied_paths]

    target_records = []
    for target_id, metadata in TARGETS.items():
        path = ROOT / metadata["path"]
        record = _image_record(path)
        if record["sha256"] != metadata["sha256"]:
            raise RuntimeError(f"Target hash mismatch: {metadata['path']}")
        record.update(
            {
                "id": target_id,
                "authority": "lower-authority generated interpretation",
                "sources": metadata["sources"],
                "accepted_for": metadata["accepted_for"],
                "rejected_for": metadata["rejected_for"],
                "verbatim_generation_prompt": metadata["verbatim_prompt"],
                "verbatim_generation_prompt_available": True,
                "prompt_provenance_note": "Verbatim prompt recovered from the parent task conversation; PNG itself contains no embedded prompt.",
            }
        )
        target_records.append(record)

    prompt_manifest = analysis / "v201_imagegen_prompt_output_manifest.json"
    write_json(
        prompt_manifest,
        {
            "schema": "v201-imagegen-manifest-v1",
            "authority_rule": "Generated plates are guidance only and never override supplied references or numeric contracts.",
            "outputs": target_records,
        },
    )

    m3_expected = None
    for line in (ROOT / "references" / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        if line.endswith("  m3/m3_chord_mapping_v2.json"):
            m3_expected = line.split()[0]
            break
    if not m3_expected or sha256(M3_JSON) != m3_expected:
        raise RuntimeError("Recovered M3 JSON does not match references/SHA256SUMS.txt")

    source_manifest = analysis / "v201_source_manifest.json"
    v200 = PHOTOREAL_CONTRACT["immutable_sources"]["V200"]
    authority_hierarchy = [
        {
            "rank": 1,
            "authority": "approved character design lock and refined turnaround",
            "paths": ["references/source/approved_character_design_lock.png", "references/turnaround/character_turnaround_v2_face_refined.png"],
        },
        {"rank": 2, "authority": "refined facial and expression sheet", "paths": ["references/facial/head_expression_sheet_v2_face_refined.png"]},
        {
            "rank": 3,
            "authority": "hand pose sheet and compact M3 hand reference",
            "paths": ["references/hands/hand_pose_sheet_v1.png", "references/hands/m3_chord_hand_v3_compact.png"],
        },
        {
            "rank": 4,
            "authority": "supplemental turnaround and approved wardrobe/prop references",
            "paths": ["references/turnaround/character_turnaround_supplemental_v3.png", *SUPPLIED_EXTRA],
        },
        {"rank": 5, "authority": "V200 scale, camera, pose and asset measurements", "paths": [v200["path"]], "sha256": v200["sha256"]},
        {"rank": 6, "authority": "generated photoreal interpretation plates; guidance only", "paths": [item["path"] for item in target_records]},
    ]
    write_json(
        source_manifest,
        {
            "schema": "v201-source-manifest-v1",
            "authority_hierarchy": authority_hierarchy,
            "supplied_images": supplied,
            "m3": {
                **m3_provenance(),
                "expected_sha256": m3_expected,
                "archive": "character_model_pack_v1_round2.zip",
                "archive_member": "character_model_pack_v1/m3/m3_chord_mapping_v2.json",
                "recovery": "unzip -j -n",
            },
            "official_base": _bundle_record(),
            "generated_manifest": str(prompt_manifest.relative_to(ROOT)),
        },
    )

    diagram = make_m3_diagram(analysis / "v201_m3_contact_diagram.png", analysis / "v201_m3_contact_geometry.json")
    return {"source_manifest": source_manifest, "prompt_manifest": prompt_manifest, "m3_diagram": diagram}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.parse_args()
    for key, path in run().items():
        print(f"{key}={path.relative_to(ROOT)} sha256={sha256(path)}")


if __name__ == "__main__":
    main()
