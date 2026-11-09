from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline import build_v203_skin_eyes as builder
from pipeline.common import sha256, write_json


builder = importlib.reload(builder)
STAGE = ROOT / "production_v203_skin_eyes"
OUTPUT = STAGE / "ant_skin_eyes_v203.blend"
TEXTURE_MANIFEST = STAGE / "analysis" / "v203_texture_manifest.json"
RENDER_MANIFEST = STAGE / "audit" / "v203_render_manifest.json"
BUILD_RECEIPT = STAGE / "audit" / "v203_build_receipt.json"
VALIDATION = STAGE / "audit" / "v203_blender_validation.json"


def main() -> None:
    builder.require(Path(bpy.data.filepath).resolve() == OUTPUT.resolve(), "Open canonical V203 before visual correction")
    manifest = json.loads(TEXTURE_MANIFEST.read_text(encoding="utf-8"))
    albedo = next(entry for entry in manifest["maps"] if entry["kind"] == "albedo")
    for tile in albedo["tiles"]:
        path = ROOT / tile["path"]
        builder.write_png16(path, int(tile["resolution"][0]), "albedo", int(tile["number"]), force=True)
        tile["sha256"] = sha256(path)
    write_json(TEXTURE_MANIFEST, manifest)
    bpy.data.images["IMG_V203_ALBEDO"].reload()

    skin = bpy.data.materials["MAT_V203_SKIN"]
    principled = skin.node_tree.nodes["V203_SKIN_PRINCIPLED"]
    principled.inputs["Subsurface Weight"].default_value = 0.075
    principled.inputs["Subsurface Scale"].default_value = 0.0015
    principled.inputs["Specular IOR Level"].default_value = 0.24
    principled.inputs["Coat Weight"].default_value = 0.01
    skin.node_tree.nodes["V203_NORMAL_MAP"].inputs["Strength"].default_value = 0.42
    skin.node_tree.nodes["V203_MICRO_BUMP"].inputs["Strength"].default_value = 0.24
    skin.node_tree.nodes["V203_MICRO_BUMP"].inputs["Distance"].default_value = 0.00022

    write_json(VALIDATION, {"status": "STALE_PENDING_VISUAL_REVALIDATION"})
    cameras = {name: bpy.data.objects[name] for name, _resolution, _denoised, _lighting in builder.RENDER_VIEWS.values()}
    renders = builder.render_suite(cameras)
    render_manifest = json.loads(RENDER_MANIFEST.read_text(encoding="utf-8"))
    render_manifest["renders"] = renders
    render_manifest["visual_correction"] = "v203-reference-brown-light-sss-v2"
    write_json(RENDER_MANIFEST, render_manifest)

    bpy.context.scene["v203_visual_correction"] = "v203-reference-brown-light-sss-v2"
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), compress=True)
    output_hash = sha256(OUTPUT)
    receipt = json.loads(BUILD_RECEIPT.read_text(encoding="utf-8"))
    receipt["output"] = {"path": str(OUTPUT.relative_to(ROOT)), "sha256": output_hash, "bytes": OUTPUT.stat().st_size}
    receipt["texture_manifest"] = {"path": str(TEXTURE_MANIFEST.relative_to(ROOT)), "sha256": sha256(TEXTURE_MANIFEST)}
    receipt["render_manifest"] = {"path": str(RENDER_MANIFEST.relative_to(ROOT)), "sha256": sha256(RENDER_MANIFEST)}
    receipt["visual_correction"] = "v203-reference-brown-light-sss-v2"
    write_json(BUILD_RECEIPT, receipt)
    print(f"V203_VISUAL_FIX_OK output_sha256={output_hash} renders={len(renders)}")


if __name__ == "__main__":
    main()
