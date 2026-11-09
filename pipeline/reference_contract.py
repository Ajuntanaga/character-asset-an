from __future__ import annotations

from pathlib import Path

from pipeline.common import project_root


REFERENCE_CONTRACT = {
    "schema": "character-reference-contract-v1",
    "authority": [
        {"id": "approved_design_lock", "path": "references/source/approved_character_design_lock.png"},
        {"id": "turnaround_v2", "path": "references/turnaround/character_turnaround_v2_face_refined.png"},
        {"id": "face_v2", "path": "references/facial/head_expression_sheet_v2_face_refined.png"},
        {"id": "turnaround_v3", "path": "references/turnaround/character_turnaround_supplemental_v3.png"},
        {"id": "hand_sheet", "path": "references/hands/hand_pose_sheet_v1.png"},
        {"id": "m3_hand_v3", "path": "references/hands/m3_chord_hand_v3_compact.png"},
    ],
    "identity_locks": {
        "hair_part": "anatomical_left_only",
        "glasses": False,
        "mouth": "closed_neutral",
        "gaze": "tired_focused_off_axis",
        "mustache_gap": "central",
        "brow_dot": "single_low_center",
    },
    "wardrobe_locks": {
        "shirt": "fully_buttoned_dark_floral",
        "jacket": "charcoal_work_jacket",
        "pen": "anatomical_left_chest",
        "trousers": "matte_true_black_rolled_cuffs",
        "boots": "brown_leather_chelsea",
    },
    "m3": {"home_frets": [9, 10, 11, 12], "thumb": "rear_hidden"},
    "normalized_landmarks": {
        "front": {
            "chin_z": [0.290, 0.320],
            "mouth_z": [0.405, 0.440],
            "nose_base_z": [0.485, 0.520],
            "eye_line_z": [0.600, 0.635],
            "brow_line_z": [0.655, 0.690],
            "hairline_z": [0.755, 0.800],
            "face_half_width": [0.285, 0.325],
            "ear_outer_half_width": [0.345, 0.385],
        },
        "profile": {
            "nose_projection": [0.110, 0.150],
            "chin_projection": [0.055, 0.090],
            "occiput_projection": [0.190, 0.240],
        },
    },
}


def validate_reference_contract(root: Path | None = None) -> list[str]:
    root = root or project_root()
    errors: list[str] = []
    for item in REFERENCE_CONTRACT["authority"]:
        if not (root / item["path"]).is_file():
            errors.append(f"missing:{item['path']}")
    locks = REFERENCE_CONTRACT["identity_locks"]
    if locks.get("hair_part") != "anatomical_left_only":
        errors.append("invalid:hair_part")
    if locks.get("glasses") is not False:
        errors.append("invalid:glasses")
    if REFERENCE_CONTRACT["m3"].get("home_frets") != [9, 10, 11, 12]:
        errors.append("invalid:m3_home_frets")
    if REFERENCE_CONTRACT["m3"].get("thumb") != "rear_hidden":
        errors.append("invalid:m3_thumb")
    return errors
