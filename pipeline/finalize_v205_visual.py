from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline import build_v205_wardrobe as build
from pipeline.common import sha256, write_json


STAGE = ROOT / "production_v205_wardrobe"
OUTPUT = STAGE / "ant_wardrobe_boots_v205.blend"


def main() -> None:
    build.require(bpy.context.scene.get("checkpoint") == "V205_WARDROBE_BOOTS", "V205 must be open")
    build.require(Path(bpy.data.filepath).resolve() == OUTPUT.resolve(), "Finalizer must target canonical V205")

    for side in ("L", "R"):
        toe = bpy.data.objects[f"V205_BOOT_TOE_{side}"]
        if not toe.get("v205_final_toe_proportions"):
            for vertex in toe.data.vertices:
                vertex.co.x *= 0.88
                vertex.co.y *= 1.02
                vertex.co.z *= 0.75
            toe.location.y = -0.105
            toe.data.update()
            toe["v205_final_toe_proportions"] = True

    sole = bpy.data.materials["MAT_V205_BOOT_SOLE"]
    principled = sole.node_tree.nodes.get("Principled BSDF")
    if principled is not None:
        principled.inputs["Base Color"].default_value = (0.0012, 0.0012, 0.0010, 1.0)
        principled.inputs["Roughness"].default_value = 0.86
    sole.diffuse_color = (0.0012, 0.0012, 0.0010, 1.0)

    scene = bpy.context.scene
    scene["v205_visual_acceptance_revision"] = "continuous fitted shells; flattened Chelsea toes; enclosed ankle transition; blockouts hidden"
    audit_path = STAGE / "audit" / "v205_wardrobe_audit.json"
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    audit["visual_acceptance_revision"] = scene["v205_visual_acceptance_revision"]
    audit["visible_acceptance_objects"] = sorted(
        obj.name for obj in bpy.data.objects if obj.get("v205_procedural_final") is True and not obj.hide_render
    )
    audit["rejected_passes"] = [
        "detached horizontal sleeves and exposed ankle anatomy",
        "body-aligned blockout sleeves with box boots",
        "fitted cloth shells with missing sculpted boot toe and shaft",
    ]
    write_json(audit_path, audit)

    cameras = {name: bpy.data.objects[name] for name in (
        "V205_CAM_FRONT", "V205_CAM_THREE_QUARTER", "V205_CAM_PROFILE",
        "V205_CAM_REAR", "V205_CAM_TORSO", "V205_CAM_BOOTS",
    )}
    renders = build.render_suite(cameras)
    manifest_path = STAGE / "audit" / "v205_render_manifest.json"
    write_json(manifest_path, {"schema": "v205-render-manifest-v1", "checkpoint": "V205_WARDROBE_BOOTS", "renderer": "Cycles CPU", "renders": renders})
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), compress=True)
    output_hash = sha256(OUTPUT)
    receipt_path = STAGE / "audit" / "v205_build_receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["output"] = {"path": str(OUTPUT.relative_to(ROOT)), "sha256": output_hash, "bytes": OUTPUT.stat().st_size}
    receipt["wardrobe_audit"] = {"path": str(audit_path.relative_to(ROOT)), "sha256": sha256(audit_path)}
    receipt["render_manifest"] = {"path": str(manifest_path.relative_to(ROOT)), "sha256": sha256(manifest_path)}
    receipt["visual_acceptance_revision"] = scene["v205_visual_acceptance_revision"]
    write_json(receipt_path, receipt)
    print(f"V205_VISUAL_FINAL_OK sha256={output_hash} renders={len(renders)}")


if __name__ == "__main__":
    main()
