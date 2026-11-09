from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.common import sha256, write_json
from pipeline.photoreal_contract import PHOTOREAL_CONTRACT, validate_photoreal_contract


STAGE = ROOT / "production_v201_reference_lock"
OUTPUT = STAGE / "ant_photoreal_reference_v201.blend"
BUILDING = STAGE / ".ant_photoreal_reference_v201.building.blend"
BUNDLE = ROOT / "third_party" / "blender_human_base_meshes" / "v1.4.1" / "human-base-meshes-bundle-v1.4.1" / "human_base_meshes_bundle.blend"
BUNDLE_ARCHIVE = ROOT / "third_party" / "blender_human_base_meshes" / "v1.4.1" / "human-base-meshes-bundle-v1.4.1.zip"
SOURCE_ASSET = "Body Male - Realistic"
BASE_COLLECTION = "V201_BASE_OFFICIAL_REALISTIC_MALE"
REFERENCE_COLLECTION = "V201_REFERENCE_IMAGES"
BODY_NAME = "V201_BASE_BODY_REALISTIC_MALE"
EXPECTED_ARCHIVE_SHA256 = "811f43accbb31a88266d932f8f5563b2d13586fca0ba2693aad1f5fe582b3515"

REFERENCE_IMAGES = [
    "references/source/approved_character_design_lock.png",
    "references/turnaround/character_turnaround_v2_face_refined.png",
    "references/turnaround/character_turnaround_supplemental_v3.png",
    "references/facial/head_expression_sheet_v2_face_refined.png",
    "references/hands/hand_pose_sheet_v1.png",
    "references/hands/m3_chord_hand_v3_compact.png",
    "references/props/strandberg/strandberg_full_product.jpg",
    "references/props/strandberg/strandberg_angle.jpg",
    "references/props/strandberg/strandberg_control_closeup.jpg",
    "references/props/strandberg/user_colorway.png",
    "production_v201_reference_lock/targets/v201_photoreal_face_target_v1.png",
    "production_v201_reference_lock/targets/v201_photoreal_fullbody_target_v1.png",
    "production_v201_reference_lock/targets/v201_photoreal_guitar_target_v1.png",
    "production_v201_reference_lock/targets/v201_photoreal_m3_hand_target_v1.png",
    "production_v201_reference_lock/analysis/v201_m3_contact_diagram.png",
]


def activate(obj: bpy.types.Object) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def bounds(objects: list[bpy.types.Object]) -> tuple[Vector, Vector]:
    points = [obj.matrix_world @ Vector(corner) for obj in objects if obj.type == "MESH" for corner in obj.bound_box]
    if not points:
        raise RuntimeError("No mesh bounds available")
    return (
        Vector(tuple(min(point[index] for point in points) for index in range(3))),
        Vector(tuple(max(point[index] for point in points) for index in range(3))),
    )


def append_official_base() -> tuple[bpy.types.Collection, list[bpy.types.Object], dict[str, object]]:
    if sha256(BUNDLE_ARCHIVE) != EXPECTED_ARCHIVE_SHA256:
        raise RuntimeError("Official base archive hash mismatch")
    with bpy.data.libraries.load(str(BUNDLE), link=False, assets_only=True) as (source, destination):
        if SOURCE_ASSET not in source.collections:
            raise RuntimeError(f"Official asset is missing: {SOURCE_ASSET}")
        destination.collections = [SOURCE_ASSET]
    collection = bpy.data.collections.get(SOURCE_ASSET)
    if collection is None:
        raise RuntimeError("Official realistic male collection did not append")
    asset_metadata = collection.asset_data
    source_record = {
        "asset_name": SOURCE_ASSET,
        "author": asset_metadata.author if asset_metadata else "",
        "description": asset_metadata.description if asset_metadata else "",
        "license": asset_metadata.license if asset_metadata else "",
        "catalog_id": str(asset_metadata.catalog_id) if asset_metadata else "",
    }
    if source_record["license"] != "CC0":
        raise RuntimeError(f"Unexpected official asset license: {source_record['license']}")
    bpy.context.scene.collection.children.link(collection)
    bpy.context.view_layer.update()
    collection.name = BASE_COLLECTION
    objects = list(collection.all_objects)
    by_original_name = {obj.name: obj for obj in objects}
    body = by_original_name.get("GEO-body_male_realistic")
    if body is None or body.type != "MESH":
        raise RuntimeError("Official realistic male body is missing")
    body.name = BODY_NAME
    body.data.name = BODY_NAME + "_MESH"
    for original, renamed in (
        ("GEO-body_male_realistic.eye.L", "V201_BASE_EYE_L"),
        ("GEO-body_male_realistic.eye.R", "V201_BASE_EYE_R"),
    ):
        obj = by_original_name.get(original)
        if obj:
            obj.name = renamed
            obj.data.name = renamed + "_MESH"
    collection["source_asset_name"] = SOURCE_ASSET
    collection["source_blend"] = str(BUNDLE.relative_to(ROOT))
    collection["source_blend_sha256"] = sha256(BUNDLE)
    collection["source_archive_sha256"] = sha256(BUNDLE_ARCHIVE)
    collection["source_author"] = source_record["author"]
    collection["source_license"] = source_record["license"]
    collection["source_description"] = source_record["description"]
    return collection, objects, source_record


def normalize_base(objects: list[bpy.types.Object]) -> dict[str, float]:
    mesh_objects = [obj for obj in objects if obj.type == "MESH"]
    before_min, before_max = bounds(mesh_objects)
    source_height = before_max.z - before_min.z
    scale = float(PHOTOREAL_CONTRACT["character_height_m"]) / source_height
    parent_map = [(obj, obj.parent) for obj in objects if obj.parent is not None]
    for obj, _parent in parent_map:
        world = obj.matrix_world.copy()
        obj.parent = None
        obj.matrix_world = world
    for obj in objects:
        obj.matrix_world = Matrix.Scale(scale, 4) @ obj.matrix_world
    for obj in mesh_objects:
        activate(obj)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    scaled_min, scaled_max = bounds(mesh_objects)
    center_x = (scaled_min.x + scaled_max.x) / 2.0
    center_y = (scaled_min.y + scaled_max.y) / 2.0
    translation = Vector((-center_x, -center_y, -scaled_min.z))
    for obj in objects:
        obj.location += translation
    for obj, parent in parent_map:
        world = obj.matrix_world.copy()
        obj.parent = parent
        obj.matrix_world = world
    bpy.context.view_layer.update()
    final_min, final_max = bounds(mesh_objects)
    height = final_max.z - final_min.z
    if abs(height - 1.80) > 1e-4:
        raise RuntimeError(f"Height normalization failed: {height}")
    return {
        "source_height_m": float(source_height),
        "scale_factor": float(scale),
        "height_m": float(height),
        "width_m": float(final_max.x - final_min.x),
        "depth_m": float(final_max.y - final_min.y),
        "min_z_m": float(final_min.z),
        "max_z_m": float(final_max.z),
        "arm_span_to_height": float((final_max.x - final_min.x) / height),
    }


def add_references() -> dict[str, str]:
    collection = bpy.data.collections.new(REFERENCE_COLLECTION)
    bpy.context.scene.collection.children.link(collection)
    collection.hide_render = True
    collection["authority"] = "supplied references first; generated plates lower authority"
    records: dict[str, str] = {}
    for index, relative in enumerate(REFERENCE_IMAGES):
        path = ROOT / relative
        if not path.is_file():
            raise FileNotFoundError(path)
        image = bpy.data.images.load(str(path), check_existing=False)
        image.name = f"V201_REFERENCE_{index:02d}_{path.stem}"
        image.filepath = bpy.path.relpath(str(path), start=str(OUTPUT.parent))
        bpy.ops.object.empty_add(type="IMAGE")
        obj = bpy.context.object
        for owner in list(obj.users_collection):
            owner.objects.unlink(obj)
        collection.objects.link(obj)
        obj.name = image.name
        obj.data = image
        obj.empty_display_size = 1.0
        obj.hide_render = True
        obj.location = ((index % 5 - 2) * 2.2, 4.0 + (index // 5) * 0.1, 1.0 + (index // 5) * 2.2)
        obj.rotation_euler = (math.radians(90.0), 0.0, 0.0)
        records[relative] = sha256(path)
    return records


def material(name: str, color: tuple[float, float, float, float], roughness: float) -> bpy.types.Material:
    value = bpy.data.materials.new(name)
    value.use_nodes = True
    principled = value.node_tree.nodes.get("Principled BSDF")
    principled.inputs["Base Color"].default_value = color
    principled.inputs["Roughness"].default_value = roughness
    return value


def look_at(obj: bpy.types.Object, target: Vector) -> None:
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def add_camera(name: str, location: tuple[float, float, float], target: Vector) -> bpy.types.Object:
    data = bpy.data.cameras.new(name + "_DATA")
    data.type = "ORTHO"
    data.ortho_scale = 2.08
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = location
    look_at(obj, target)
    return obj


def add_area(name: str, location: tuple[float, float, float], energy: float, size: float, target: Vector) -> None:
    data = bpy.data.lights.new(name + "_DATA", "AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = location
    look_at(obj, target)


def configure_stage(base_objects: list[bpy.types.Object]) -> dict[str, bpy.types.Object]:
    scene = bpy.context.scene
    scene.name = "V201_PHOTOREAL_REFERENCE_SCENE"
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 24
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = 0.02
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 540
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.render.image_settings.color_mode = "RGBA"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.world = scene.world or bpy.data.worlds.new("V201_STUDIO_WORLD")
    scene.world.color = (0.018, 0.022, 0.028)
    scene.render.image_settings.color_depth = "8"

    clay = material("V201_INSPECTION_CLAY", (0.24, 0.115, 0.060, 1.0), 0.54)
    bpy.context.view_layer.material_override = clay

    bpy.ops.mesh.primitive_plane_add(size=8.0, location=(0.0, 0.0, -0.002))
    floor = bpy.context.object
    floor.name = "V201_INSPECTION_FLOOR"
    floor.data.materials.append(material("V201_FLOOR_MAT", (0.055, 0.065, 0.078, 1.0), 0.68))

    target = Vector((0.0, 0.0, 0.91))
    cameras = {
        "front": add_camera("V201_CAM_FRONT", (0.0, -4.0, 0.91), target),
        "profile": add_camera("V201_CAM_PROFILE", (4.0, 0.0, 0.91), target),
        "three_quarter": add_camera("V201_CAM_THREE_QUARTER", (3.0, -3.0, 0.97), target),
        "back": add_camera("V201_CAM_BACK", (0.0, 4.0, 0.91), target),
    }
    add_area("V201_KEY", (2.7, -3.6, 4.2), 780.0, 3.0, target)
    add_area("V201_FILL", (-3.0, -1.8, 2.7), 430.0, 2.5, target)
    add_area("V201_RIM", (1.5, 3.0, 3.4), 650.0, 2.2, target)
    return cameras


def render_inspections(cameras: dict[str, bpy.types.Object]) -> dict[str, str]:
    scene = bpy.context.scene
    render_dir = STAGE / "renders" / "base_inspection"
    render_dir.mkdir(parents=True, exist_ok=True)
    outputs: dict[str, str] = {}
    for label, camera in cameras.items():
        scene.camera = camera
        scene.render.filepath = f"//renders/base_inspection/{label}.png"
        bpy.ops.render.render(write_still=True)
        path = render_dir / f"{label}.png"
        if not path.is_file():
            raise RuntimeError(f"Render missing: {path}")
        outputs[label] = sha256(path)
    return outputs


def main() -> None:
    if OUTPUT.exists():
        raise FileExistsError(f"Refusing to overwrite immutable checkpoint: {OUTPUT}")
    errors = validate_photoreal_contract(ROOT)
    if errors:
        raise RuntimeError(f"Photoreal contract errors: {errors}")
    if tuple(bpy.app.version) < (5, 2, 2):
        raise RuntimeError(f"Blender 5.2.2+ required, got {bpy.app.version_string}")
    bpy.ops.wm.read_factory_settings(use_empty=True)
    collection, objects, source_record = append_official_base()
    metrics = normalize_base(objects)
    reference_hashes = add_references()
    cameras = configure_stage(objects)

    scene = bpy.context.scene
    scene["checkpoint"] = "V201_PHOTOREAL_REFERENCE"
    scene["stage"] = "V201"
    scene["character_height_m"] = 1.80
    scene["base_collection"] = BASE_COLLECTION
    scene["base_source_asset"] = SOURCE_ASSET
    scene["base_source_path"] = str(BUNDLE.relative_to(ROOT))
    scene["base_source_sha256"] = sha256(BUNDLE)
    scene["base_archive_path"] = str(BUNDLE_ARCHIVE.relative_to(ROOT))
    scene["base_archive_sha256"] = sha256(BUNDLE_ARCHIVE)
    scene["base_license"] = source_record["license"]
    scene["base_author"] = source_record["author"]
    scene["reference_hashes_json"] = json.dumps(reference_hashes, sort_keys=True)
    scene["base_metrics_json"] = json.dumps(metrics, sort_keys=True)
    scene["neutral_pose_evidence_json"] = json.dumps(
        {
            "pose": "official_neutral_A_pose",
            "evidence": "official Body Male - Realistic asset plus four orthographic inspection renders",
            "arm_span_to_height": metrics["arm_span_to_height"],
            "arms_laterally_extended": metrics["arm_span_to_height"] > 0.45,
            "feet_on_ground": abs(metrics["min_z_m"]) <= 1e-5,
            "destructive_pose_edit": False,
        },
        sort_keys=True,
    )
    scene["identity_authority"] = "supplied references; generated plates lower authority"
    scene["m3_geometry_authority"] = "references/m3/m3_chord_mapping_v2.json and PHOTOREAL_CONTRACT"
    scene["v200_geometry_imported"] = False

    STAGE.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(BUILDING), check_existing=False)
    render_hashes = render_inspections(cameras)
    scene["inspection_render_hashes_json"] = json.dumps(render_hashes, sort_keys=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    if BUILDING.exists():
        BUILDING.unlink()

    write_json(
        STAGE / "audit" / "v201_build_receipt.json",
        {
            "schema": "v201-build-receipt-v1",
            "checkpoint": "V201_PHOTOREAL_REFERENCE",
            "blender_version": bpy.app.version_string,
            "render_engine": "CYCLES",
            "cycles_device": "CPU",
            "source": source_record,
            "metrics": metrics,
            "reference_hashes": reference_hashes,
            "render_hashes": render_hashes,
            "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha256(OUTPUT), "bytes": OUTPUT.stat().st_size},
            "status": "PASS",
        },
    )
    print(f"V201_BUILD_OK {OUTPUT} sha256={sha256(OUTPUT)}")


if __name__ == "__main__":
    main()
