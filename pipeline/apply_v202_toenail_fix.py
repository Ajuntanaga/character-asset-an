from __future__ import annotations

import json
import importlib
import sys
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline import build_v202_neutral_anatomy as _v202_builder
from pipeline.common import sha256, write_json


_v202_builder = importlib.reload(_v202_builder)
OUTPUT = _v202_builder.OUTPUT
RENDER_VIEWS = _v202_builder.RENDER_VIEWS
STAGE = _v202_builder.STAGE
rebuild_toenails = _v202_builder.rebuild_toenails
require = _v202_builder.require


BUILD_RECEIPT = STAGE / "audit" / "v202_build_receipt.json"
VALIDATION = STAGE / "audit" / "v202_blender_validation.json"
MEASUREMENTS = STAGE / "analysis" / "v202_landmark_measurements.json"
RENDER_MANIFEST = STAGE / "audit" / "v202_render_manifest.json"
PATCH_RECEIPT = STAGE / "audit" / "v202_review_fix_receipt.json"
FIX_VERSION = "v202-distal-normal-raycast-toenails-v5"
FOOT_VIEWS = ("feet", "foot_left", "foot_right")


def object_center(obj: bpy.types.Object) -> Vector:
    points = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
    minimum = Vector(tuple(min(point[index] for point in points) for index in range(3)))
    maximum = Vector(tuple(max(point[index] for point in points) for index in range(3)))
    return (minimum + maximum) / 2.0


def render_foot_views() -> dict[str, dict[str, object]]:
    scene = bpy.context.scene
    clay_dir = STAGE / "renders" / "clay"
    results: dict[str, dict[str, object]] = {}
    for label in FOOT_VIEWS:
        camera_name, resolution = RENDER_VIEWS[label]
        scene.camera = bpy.data.objects[camera_name]
        scene.render.resolution_x, scene.render.resolution_y = resolution
        scene.render.resolution_percentage = 100
        path = clay_dir / f"{label}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        require(path.is_file(), f"Missing rerender: {path}")
        results[label] = {
            "path": str(path.relative_to(ROOT)),
            "sha256": sha256(path),
            "resolution": list(resolution),
            "engine": "CYCLES",
            "device": "CPU",
        }
    return results


def main() -> None:
    require(Path(bpy.data.filepath).resolve() == OUTPUT.resolve(), f"Open canonical V202 before patching: {OUTPUT}")
    require(OUTPUT.is_file() and BUILD_RECEIPT.is_file(), "Canonical V202 or build receipt missing")
    require(bpy.context.scene.get("v202_review_fix") == "v202-supplied-reference-match-v2", "Reference-match correction is not present")
    require(bpy.context.scene.get("v202_toenail_review_fix") != FIX_VERSION, "Distal toenail correction already applied")

    pre_hash = sha256(OUTPUT)
    receipt = json.loads(BUILD_RECEIPT.read_text(encoding="utf-8"))
    require(receipt.get("output", {}).get("sha256") == pre_hash, "Pre-fix build receipt is stale")

    body = bpy.data.objects.get("V202_BODY")
    anatomy = bpy.data.collections.get("V202_ANATOMY")
    nail_material = bpy.data.materials.get("MAT_V202_NAIL_PLATE")
    require(body is not None and body.type == "MESH", "V202_BODY missing")
    require(anatomy is not None and nail_material is not None, "V202 anatomy or nail material missing")

    toe_objects = rebuild_toenails(body, anatomy, nail_material)
    require(len(toe_objects) == 10, f"Expected ten rebuilt toenails, found {len(toe_objects)}")
    bpy.context.view_layer.update()
    bpy.context.scene["v202_toenail_review_fix"] = FIX_VERSION

    measurements = json.loads(MEASUREMENTS.read_text(encoding="utf-8"))
    measurements["organ_centers_m"] = {
        obj.name: [round(value, 6) for value in object_center(obj)]
        for obj in anatomy.all_objects
        if obj.type == "MESH"
    }
    measurements["toenail_review_fix"] = {
        "version": FIX_VERSION,
        "method": "per-digit distal dorsal seeds plus multi-sample evaluated-body surface conformance",
        "objects": [obj.name for obj in toe_objects],
    }
    write_json(MEASUREMENTS, measurements)

    write_json(
        VALIDATION,
        {
            "schema": "v202-blender-validation-v1",
            "status": "STALE_PENDING_REVALIDATION",
            "reason": "canonical V202 toenail geometry changed after visual gate",
            "pre_fix_output_sha256": pre_hash,
        },
    )

    updated_renders = render_foot_views()
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), compress=True)
    output_hash = sha256(OUTPUT)

    render_manifest = json.loads(RENDER_MANIFEST.read_text(encoding="utf-8"))
    render_manifest["renders"].update(updated_renders)
    render_manifest["canonical_output"] = {"path": str(OUTPUT.relative_to(ROOT)), "sha256": output_hash}
    render_manifest["toenail_review_fix"] = FIX_VERSION
    write_json(RENDER_MANIFEST, render_manifest)

    receipt["output"] = {"path": str(OUTPUT.relative_to(ROOT)), "sha256": output_hash, "bytes": OUTPUT.stat().st_size}
    receipt["render_manifest"] = {"path": str(RENDER_MANIFEST.relative_to(ROOT)), "sha256": sha256(RENDER_MANIFEST)}
    receipt["measurement_record"] = {"path": str(MEASUREMENTS.relative_to(ROOT)), "sha256": sha256(MEASUREMENTS)}
    receipt["pre_toenail_fix_output_sha256"] = pre_hash
    receipt["toenail_review_fix"] = FIX_VERSION
    write_json(BUILD_RECEIPT, receipt)

    patch_receipt = json.loads(PATCH_RECEIPT.read_text(encoding="utf-8")) if PATCH_RECEIPT.is_file() else {}
    patch_receipt.update(
        {
            "status": "PASS_PENDING_CLEAN_REOPEN_VALIDATION",
            "output": receipt["output"],
            "build_receipt_sha256": sha256(BUILD_RECEIPT),
            "measurement_record_sha256": sha256(MEASUREMENTS),
            "render_manifest_sha256": sha256(RENDER_MANIFEST),
            "toenail_review_fix": FIX_VERSION,
            "toenail_objects": [obj.name for obj in toe_objects],
            "required_next_step": "clean-reopen pipeline/tests/blender_validate_v202.py against canonical OUTPUT",
        }
    )
    write_json(PATCH_RECEIPT, patch_receipt)
    print(
        f"V202_TOENAIL_FIX_OK output_sha256={output_hash} "
        f"toenails={len(toe_objects)} rerenders={len(updated_renders)} validation=STALE_PENDING_REVALIDATION"
    )


if __name__ == "__main__":
    main()
