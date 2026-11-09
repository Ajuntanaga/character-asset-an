from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.build_v202_neutral_anatomy import (
    EXPECTED_SOURCE_SHA256,
    EXPECTED_V192_SHA256,
    EXPECTED_V200_SHA256,
    OUTPUT,
    RENDER_VIEWS,
    SOURCE,
    STAGE,
    apply_reference_match_delta,
    capture_measurements,
    rebuild_toenails,
    render_suite,
    require,
)
from pipeline.common import sha256, write_json
from pipeline.photoreal_contract import PHOTOREAL_CONTRACT


BUILD_RECEIPT = STAGE / "audit" / "v202_build_receipt.json"
VALIDATION = STAGE / "audit" / "v202_blender_validation.json"
MEASUREMENTS = STAGE / "analysis" / "v202_landmark_measurements.json"
RENDER_MANIFEST = STAGE / "audit" / "v202_render_manifest.json"
PATCH_RECEIPT = STAGE / "audit" / "v202_review_fix_receipt.json"


def object_center(obj: bpy.types.Object) -> Vector:
    points = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
    minimum = Vector(tuple(min(point[index] for point in points) for index in range(3)))
    maximum = Vector(tuple(max(point[index] for point in points) for index in range(3)))
    return (minimum + maximum) / 2.0


def main() -> None:
    require(tuple(bpy.app.version) >= (5, 2, 2), f"Blender 5.2.2+ required: {bpy.app.version_string}")
    require(Path(bpy.data.filepath).resolve() == OUTPUT.resolve(), f"Open canonical V202 before patching: {OUTPUT}")
    require(OUTPUT.is_file() and BUILD_RECEIPT.is_file(), "Canonical V202 or its build receipt is missing")
    pre_hash = sha256(OUTPUT)
    previous_receipt = json.loads(BUILD_RECEIPT.read_text(encoding="utf-8"))
    require(previous_receipt.get("output", {}).get("sha256") == pre_hash, "Pre-patch V202 build receipt is already stale")

    body = bpy.data.objects.get("V202_BODY")
    anatomy = bpy.data.collections.get("V202_ANATOMY")
    nail_material = bpy.data.materials.get("MAT_V202_NAIL_PLATE")
    require(body is not None and body.type == "MESH", "V202_BODY missing")
    require(anatomy is not None and nail_material is not None, "V202 anatomy or nail material missing")
    require(body.get("reference_match_correction") != "v202-supplied-reference-match-v2", "Review fix already applied to this scene")

    before_review = capture_measurements(body)
    correction = apply_reference_match_delta(body)
    toe_objects = rebuild_toenails(body, anatomy, nail_material)
    bpy.context.view_layer.update()
    after = capture_measurements(body)

    existing = json.loads(MEASUREMENTS.read_text(encoding="utf-8")) if MEASUREMENTS.is_file() else {}
    original_before = existing.get("before", {})
    for band_name in ("neck", "upper_torso"):
        original_before[band_name] = before_review[band_name]
    measurements = {
        "schema": "v202-landmark-measurements-v1",
        "checkpoint": "V202_NEUTRAL_ANATOMY",
        "source_v201_sha256": EXPECTED_SOURCE_SHA256,
        "deformation_method": "smooth topology-space anatomical fields",
        "height_lock_m": 1.80,
        "before": original_before,
        "review_before": before_review,
        "after": after,
        "proportion_deltas": {
            key: {
                metric: after[key][metric] - original_before[key][metric]
                for metric in ("width_m", "depth_m")
            }
            for key in ("head", "midface", "jaw", "neck", "upper_torso", "chest", "waist", "hips", "thighs")
        },
        "review_correction": correction,
        "identity_fields": [
            "slim compact oval head with preserved cheek breadth and tapered jaw/chin",
            "broader rounded natural alar base",
            "fuller sealed upper and lower lips",
            "narrowed neck/trapezius and average-to-lean torso, shoulder, chest, and thigh mass",
            "thin crowned toe plates rebuilt from evaluated V202_BODY raycasts",
        ],
        "organ_centers_m": {
            obj.name: [round(value, 6) for value in object_center(obj)]
            for obj in anatomy.all_objects
            if obj.type == "MESH"
        },
        "reference_authority": "supplied face sheet and turnaround authoritative; generated photoreal target explicitly lower-authority guidance",
    }
    write_json(MEASUREMENTS, measurements)
    bpy.context.scene["landmark_measurements_json"] = json.dumps(measurements["proportion_deltas"], sort_keys=True)
    bpy.context.scene["identity_authority"] = "supplied design lock, refined turnaround, and face sheet; generated plates lower-authority guidance"
    bpy.context.scene["v202_review_fix"] = correction["version"]

    # Invalidate the previous PASS before producing new images/checkpoint.
    write_json(
        VALIDATION,
        {
            "schema": "v202-blender-validation-v1",
            "status": "STALE_PENDING_REVALIDATION",
            "reason": "canonical V202 changed by supplied-reference and nail-plate review fix",
            "pre_patch_output_sha256": pre_hash,
        },
    )

    cameras = {name: bpy.data.objects[name] for name, _resolution in RENDER_VIEWS.values()}
    cameras["V202_CAM_TOPOLOGY_FRONT"] = bpy.data.objects["V202_CAM_TOPOLOGY_FRONT"]
    render_results = render_suite(body, cameras)

    # Save directly because this script is specifically an MCP patch for the
    # open canonical file; the caller retains the already accepted V201 source.
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), compress=True)
    output_hash = sha256(OUTPUT)
    render_manifest = {
        "schema": "v202-render-manifest-v1",
        "status": "PASS",
        "checkpoint": "V202_NEUTRAL_ANATOMY",
        "renderer": "Cycles CPU",
        "color_management": "AgX - Medium High Contrast",
        "samples": bpy.context.scene.cycles.samples,
        "long_edge_px": 1600,
        "renders": render_results,
        "canonical_output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": output_hash},
        "review_fix": correction["version"],
    }
    write_json(RENDER_MANIFEST, render_manifest)

    immutable = {}
    for version, expected in (("V201", EXPECTED_SOURCE_SHA256), ("V200", EXPECTED_V200_SHA256), ("V192", EXPECTED_V192_SHA256)):
        path = SOURCE if version == "V201" else ROOT / PHOTOREAL_CONTRACT["immutable_sources"][version]["path"]
        require(path.is_file() and sha256(path) == expected, f"Immutable {version} changed")
        immutable[version] = {"path": str(path.relative_to(ROOT)), "sha256": sha256(path)}

    build_receipt = {
        "schema": "v202-build-receipt-v1",
        "status": "PASS",
        "checkpoint": "V202_NEUTRAL_ANATOMY",
        "blender_version": bpy.app.version_string,
        "source": immutable["V201"],
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": output_hash, "bytes": OUTPUT.stat().st_size},
        "immutable_sources": immutable,
        "body": {
            "vertices": len(body.data.vertices),
            "polygons": len(body.data.polygons),
            "uv_layers": len(body.data.uv_layers),
            "multires_total_levels": next(modifier.total_levels for modifier in body.modifiers if modifier.type == "MULTIRES"),
        },
        "anatomy_object_count": len(anatomy.all_objects),
        "camera_count": len([obj for obj in bpy.data.objects if obj.type == "CAMERA"]),
        "dependency_count": previous_receipt.get("dependency_count", 0),
        "dependencies": previous_receipt.get("dependencies", []),
        "render_manifest": {"path": str(RENDER_MANIFEST.relative_to(ROOT)), "sha256": sha256(RENDER_MANIFEST)},
        "measurement_record": {"path": str(MEASUREMENTS.relative_to(ROOT)), "sha256": sha256(MEASUREMENTS)},
        "review_fix": correction,
        "pre_patch_output_sha256": pre_hash,
    }
    write_json(BUILD_RECEIPT, build_receipt)
    patch_receipt = {
        "schema": "v202-review-fix-receipt-v1",
        "status": "PASS_PENDING_CLEAN_REOPEN_VALIDATION",
        "pre_patch_output_sha256": pre_hash,
        "output": build_receipt["output"],
        "build_receipt_sha256": sha256(BUILD_RECEIPT),
        "measurement_record_sha256": sha256(MEASUREMENTS),
        "render_manifest_sha256": sha256(RENDER_MANIFEST),
        "correction": correction,
        "toenail_objects": [obj.name for obj in toe_objects],
        "required_next_step": "clean-reopen pipeline/tests/blender_validate_v202.py against canonical OUTPUT",
    }
    write_json(PATCH_RECEIPT, patch_receipt)
    print(f"V202_REVIEW_FIX_OK output_sha256={output_hash} toenails={len(toe_objects)} renders={len(render_results)} validation=STALE_PENDING_REVALIDATION")


if __name__ == "__main__":
    main()
