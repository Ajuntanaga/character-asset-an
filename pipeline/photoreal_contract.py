from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from pipeline.common import project_root, sha256
from pipeline.reference_contract import REFERENCE_CONTRACT


_STAGES = {
    "V201": "photoreal_reference_lock_and_base_intake",
    "V202": "neutral_anatomy_and_identity",
    "V203": "skin_eyes_and_facial_detail",
    "V204": "hair_and_facial_grooming",
    "V205": "wardrobe_and_boots",
    "V206": "guitar_rebuild",
    "V207": "playable_hands_and_guitar_contacts",
    "V208": "production_rig_and_deformation",
    "V209": "photoreal_look_development",
    "V210": "final_presentation_and_delivery",
}

_M3 = deepcopy(REFERENCE_CONTRACT["m3"])
_M3.update(
    {
        "string_order_low_to_high": ["S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8"],
        "tuning_low_to_high": ["B", "F", "A#", "D", "G", "C", "F", "A"],
        "scale_lengths_in_s8_to_s1": [26.50, 26.71, 26.93, 27.14, 27.36, 27.57, 27.79, 28.00],
        "neutral_fret": 7,
        "nut_spread_mm": 49.0,
        "bridge_spread_mm": 73.5,
        "frets": 24,
        "finger_targets": {"index": ["S5", 9], "middle": ["S4", 10], "ring": ["S7", 9], "pinky": ["S8", 11]},
    }
)
_EXPECTED_M3 = deepcopy(_M3)

PHOTOREAL_CONTRACT: dict[str, object] = deepcopy(REFERENCE_CONTRACT)
PHOTOREAL_CONTRACT.update(
    {
        "schema": "photoreal-contract-v1",
        "character_height_m": 1.80,
        "blender_version_floor": "5.2.2",
        "official_base_url": "https://download.blender.org/demo/asset-bundles/human-base-meshes/human-base-meshes-bundle-v1.4.1.zip",
        "immutable_sources": {
            "V200": {"path": "production_v200_final/ant_character_asset_final_v200.blend", "sha256": "42612cfbd1cbeed03c0db1eb085ea10f1ca73fe3697404ad563d1cb15599c6d1"},
            "V192": {"path": "ant_compact_pick_pinch_v192.blend", "sha256": "443321b43df4ada529113854f935b393e2e523fbbd36beb08c53fb0d08048148"},
        },
        "m3": _M3,
        "stages": _STAGES,
        "stage_names": list(_STAGES.values()),
    }
)


def validate_photoreal_contract(root: Path | None = None) -> list[str]:
    root = (root or project_root()).resolve()
    errors: list[str] = []
    for item in PHOTOREAL_CONTRACT["authority"]:
        if not (root / item["path"]).is_file():
            errors.append(f"missing:{item['path']}")
    for stage in PHOTOREAL_CONTRACT["immutable_sources"].values():
        path = root / stage["path"]
        if not path.is_file():
            errors.append(f"missing:{stage['path']}")
        elif sha256(path) != stage["sha256"]:
            errors.append(f"invalid:sha256:{stage['path']}")
    if PHOTOREAL_CONTRACT["character_height_m"] != 1.80:
        errors.append("invalid:character_height_m")
    if PHOTOREAL_CONTRACT["blender_version_floor"] != "5.2.2":
        errors.append("invalid:blender_version_floor")
    if PHOTOREAL_CONTRACT["official_base_url"] != "https://download.blender.org/demo/asset-bundles/human-base-meshes/human-base-meshes-bundle-v1.4.1.zip":
        errors.append("invalid:official_base_url")
    expected_m3 = _EXPECTED_M3
    for key in ("string_order_low_to_high", "tuning_low_to_high", "scale_lengths_in_s8_to_s1", "nut_spread_mm", "bridge_spread_mm", "frets", "neutral_fret", "finger_targets"):
        if PHOTOREAL_CONTRACT["m3"].get(key) != expected_m3[key]:
            errors.append(f"invalid:m3_{key}")
    if PHOTOREAL_CONTRACT["stages"] != _STAGES or PHOTOREAL_CONTRACT["stage_names"] != list(_STAGES.values()):
        errors.append("invalid:stages")
    return sorted(errors)
