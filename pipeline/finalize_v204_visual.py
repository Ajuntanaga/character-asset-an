from __future__ import annotations

import json
from pathlib import Path

import bpy

from pipeline import build_v204_groom as build
from pipeline.common import sha256, write_json


ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "production_v204_groom"
OUTPUT = STAGE / "ant_groomed_character_v204.blend"
def main() -> None:
    scene = bpy.context.scene
    build.require(scene.get("checkpoint") == "V204_GROOM", "V204 must be open")
    build.require(Path(bpy.data.filepath).resolve() == OUTPUT.resolve(), "Finalizer must target canonical V204")
    old = bpy.data.objects.get("V204_HAIRLINE_CURLS")
    if old is not None:
        bpy.data.objects.remove(old, do_unlink=True)

    cap = bpy.data.objects.get("V204_SCALP_SUBSTRATE")
    if cap is not None:
        bpy.data.objects.remove(cap, do_unlink=True)
    bevels = {
        "V204_HAIR_UNDERCOAT": 0.000120,
        "V204_HAIR_GUIDES": 0.000150,
        "V204_HAIR_CHILDREN_DENSE": 0.000130,
        "V204_HAIR_CHILDREN_CLUMP": 0.000160,
        "V204_HAIR_CHILDREN_FRIZZ": 0.000070,
        "V204_HAIR_FLYAWAYS": 0.000040,
        "V204_HAIR_TOP_CURLS": 0.000130,
        "V204_BEARD_GUIDES": 0.000080,
        "V204_BEARD_CHILDREN": 0.000055,
        "V204_MUSTACHE_L": 0.000070,
        "V204_MUSTACHE_R": 0.000070,
        "V204_BROWS": 0.000075,
        "V204_LASHES": 0.000035,
    }
    for name, bevel in bevels.items():
        bpy.data.objects[name].data.bevel_depth = bevel

    required_names = {
        "V204_HAIR_UNDERCOAT", "V204_HAIR_GUIDES", "V204_HAIR_CHILDREN_DENSE",
        "V204_HAIR_CHILDREN_CLUMP", "V204_HAIR_CHILDREN_FRIZZ", "V204_HAIR_FLYAWAYS",
        "V204_HAIR_TOP_CURLS", "V204_BEARD_GUIDES",
        "V204_BEARD_CHILDREN", "V204_MUSTACHE_L", "V204_MUSTACHE_R", "V204_BROWS", "V204_LASHES",
    }
    root_count = sum(len(bpy.data.objects[name].data.splines) for name in required_names)
    scene["v204_groom_layers"] = "undercoat,top_curls,guides,dense_children,clump,frizz,flyaway,beard,mustache,brows,lashes"
    scene["v204_photoreal_groom_revision"] = "artifact_free_curve_only_multilayer_curls"

    audit_path = STAGE / "audit" / "v204_groom_audit.json"
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    audit["root_count"] = root_count
    audit["curve_systems"] = {name: len(bpy.data.objects[name].data.splines) for name in sorted(required_names)}
    audit["fiber_radius_m"] = {name: bpy.data.objects[name].data.bevel_depth for name in sorted(required_names)}
    audit["scalp_substrate"] = {"status": "REJECTED_AND_REMOVED", "reason": "visible profile mask discontinuities"}
    audit["photoreal_revision"] = scene["v204_photoreal_groom_revision"]
    write_json(audit_path, audit)

    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), compress=True)
    cameras = {name: bpy.data.objects[name] for name in (
        "V204_CAM_FRONT", "V204_CAM_PROFILE", "V204_CAM_REAR",
        "V204_CAM_TOP", "V204_CAM_RIM", "V204_CAM_ROOT_MACRO",
    )}
    render_results = build.render_suite(cameras)
    manifest_path = STAGE / "audit" / "v204_render_manifest.json"
    write_json(manifest_path, {
        "schema": "v204-render-manifest-v1",
        "checkpoint": "V204_GROOM",
        "renderer": "Cycles CPU",
        "adaptive_sampling": True,
        "renders": render_results,
    })
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), compress=True)
    output_hash = sha256(OUTPUT)
    receipt_path = STAGE / "audit" / "v204_build_receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["output"] = {"path": str(OUTPUT.relative_to(ROOT)), "sha256": output_hash, "bytes": OUTPUT.stat().st_size}
    receipt["groom_audit"] = {"path": str(audit_path.relative_to(ROOT)), "sha256": sha256(audit_path)}
    receipt["render_manifest"] = {"path": str(manifest_path.relative_to(ROOT)), "sha256": sha256(manifest_path)}
    receipt["curve_systems"] = len(required_names)
    receipt["root_count"] = root_count
    receipt["photoreal_revision"] = scene["v204_photoreal_groom_revision"]
    write_json(receipt_path, receipt)
    print(f"V204_VISUAL_FINAL_OK sha256={output_hash} roots={root_count} renders={len(render_results)}")


if __name__ == "__main__":
    main()
