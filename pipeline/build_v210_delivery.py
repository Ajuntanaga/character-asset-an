from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.common import sha256, write_json


STAGE = ROOT / "delivery_v210"
SOURCE = ROOT / "production_v209_lookdev" / "ant_photoreal_lookdev_v209.blend"
OUTPUT = STAGE / "Character_An_Performance_v210.blend"
EXPECTED_SOURCE_SHA256 = "5125abb46542a9980993a6437d48212403856678428b788017c96a8e580cf86e"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> None:
    require(Path(bpy.data.filepath).resolve() == SOURCE.resolve(), f"Open accepted V209 source first: {SOURCE}")
    require(sha256(SOURCE) == EXPECTED_SOURCE_SHA256, "Accepted V209 source hash changed")
    STAGE.joinpath("audit").mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    scene["checkpoint"] = "V210_DELIVERY"
    scene["source_v209_sha256"] = EXPECTED_SOURCE_SHA256
    scene["delivery_intent"] = "complete Blender character asset with performance rig, headless eight-string guitar, and locked playing contacts"
    scene["visual_boundary"] = "physically based stylized/procedural hero; not scan-grade human photorealism"
    readme = bpy.data.texts.get("V210_DELIVERY_README") or bpy.data.texts.new("V210_DELIVERY_README")
    readme.clear()
    readme.write(
        "Character Asset_An V210 delivery\n\n"
        "Primary controls: V208_PERFORMANCE_RIG.\n"
        "Guitar root: V206_GUITAR_ROOT.\n"
        "Locked fretting targets: V207_TARGET_*; visible continuous surface: V209_FRETTING_HAND_CONTINUOUS.\n"
        "Picking control: pick_ctrl; plectrum: V208_PICK.\n"
        "Renderer: Cycles / AgX.\n"
        "Boundary: physically based procedural asset, not a scan-grade digital human.\n"
    )
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False, compress=True)
    output_hash = sha256(OUTPUT)
    artifacts = {}
    for path in sorted((ROOT / "production_v209_lookdev" / "renders" / "hero").glob("*.png")):
        artifacts[str(path.relative_to(ROOT))] = sha256(path)
    manifest = {
        "schema": "character-an-v210-delivery-v1",
        "status": "PASS",
        "runtime": bpy.app.version_string,
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": EXPECTED_SOURCE_SHA256},
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": output_hash, "bytes": OUTPUT.stat().st_size},
        "checkpoint": "V210_DELIVERY",
        "primary_objects": {
            "rig": "V208_PERFORMANCE_RIG",
            "guitar": "V206_GUITAR_ROOT",
            "fretting_surface": "V209_FRETTING_HAND_CONTINUOUS",
            "picking_surface": "V209_PICKING_HAND_CONTINUOUS",
            "sleeves": "V209_SLEEVES_CONTINUOUS",
        },
        "images": artifacts,
        "visual_boundary": scene["visual_boundary"],
    }
    write_json(STAGE / "audit" / "v210_delivery_manifest.json", manifest)
    write_json(STAGE / "audit" / "v210_build_receipt.json", {"status": "PASS", "output": manifest["output"], "manifest_sha256": sha256(STAGE / "audit" / "v210_delivery_manifest.json")})
    print(f"V210_DELIVERY_OK output_sha256={output_hash} images={len(artifacts)}")


if __name__ == "__main__":
    main()
