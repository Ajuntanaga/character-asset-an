from __future__ import annotations

import json
from pathlib import Path

import bpy

from pipeline import build_v205_wardrobe as build
from pipeline.common import sha256, write_json


ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "production_v205_wardrobe"
OUTPUT = STAGE / "ant_wardrobe_boots_v205.blend"


def remove_prefixes(prefixes: tuple[str, ...]) -> None:
    for obj in list(bpy.data.objects):
        if obj.name.startswith(prefixes):
            bpy.data.objects.remove(obj, do_unlink=True)


def main() -> None:
    build.require(bpy.context.scene.get("checkpoint") == "V205_WARDROBE_BOOTS", "V205 must be open")
    collection = bpy.data.collections["V205_WARDROBE"]
    jacket = bpy.data.materials["MAT_V205_CHARCOAL_JACKET"]
    leather = bpy.data.materials["MAT_V205_BROWN_BOOT_LEATHER"]
    elastic = bpy.data.materials["MAT_V205_BOOT_ELASTIC"]
    sole = bpy.data.materials["MAT_V205_BOOT_SOLE"]
    thread = bpy.data.materials["MAT_V205_TAILORING_THREAD"]

    remove_prefixes(("V205_JACKET_SLEEVE_", "V205_JACKET_CUFF_", "V205_BOOT_"))
    sleeve_paths = {
        "L": [(0.190, 0.000, 1.425), (0.255, -0.002, 1.355), (0.315, -0.008, 1.245), (0.375, -0.013, 1.125), (0.425, -0.018, 1.025)],
        "R": [(-0.190, 0.000, 1.425), (-0.255, -0.002, 1.355), (-0.315, -0.008, 1.245), (-0.375, -0.013, 1.125), (-0.425, -0.018, 1.025)],
    }
    for side, centers in sleeve_paths.items():
        sleeve = build.tube_along_path(
            f"V205_JACKET_SLEEVE_{side}", centers,
            [(0.082, 0.092), (0.076, 0.083), (0.068, 0.073), (0.058, 0.062), (0.052, 0.055)],
            collection, jacket, f"neutral A-pose jacket sleeve {side}",
        )
        sleeve["neutral_a_pose_axis"] = centers
        sign = 1.0 if side == "L" else -1.0
        build.tube_along_path(
            f"V205_JACKET_CUFF_{side}",
            [(sign * 0.402, -0.016, 1.073), (sign * 0.438, -0.019, 1.000)],
            [(0.055, 0.059), (0.052, 0.055)], collection, jacket, f"jacket cuff {side}", 24,
        )
    build.build_boots(collection, leather, elastic, sole, thread)

    jacket_body = bpy.data.objects["V205_JACKET_BODY"]
    for vertex in jacket_body.data.vertices:
        if vertex.co.z > 1.405:
            vertex.co.x *= 1.10
    jacket_body.data.update()

    scene = bpy.context.scene
    scene["v205_fit_revision"] = "body-silhouette-following sleeves; enclosed ankle transitions; widened shoulder join"
    audit_path = STAGE / "audit" / "v205_wardrobe_audit.json"
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    audit["fit_revision"] = scene["v205_fit_revision"]
    audit["rejected_first_pass"] = "floating sleeves, exposed ankle anatomy, box-like shoulder join"
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
    receipt["fit_revision"] = scene["v205_fit_revision"]
    write_json(receipt_path, receipt)
    print(f"V205_FIT_REPAIR_OK sha256={output_hash} renders={len(renders)}")


if __name__ == "__main__":
    main()
