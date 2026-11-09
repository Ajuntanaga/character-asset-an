from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
STAGE = ROOT / "production_v211_clean_base"
BLEND_OUT = STAGE / "Character_An_clean_base_v211.blend"
AUDIT_OUT = STAGE / "audit/v211_base_manifest.json"
RENDER_DIR = STAGE / "renders/alignment"
ARCHIVE = ROOT / "third_party/blender_human_base_meshes/v1.4.1/human-base-meshes-bundle-v1.4.1.zip"
LIBRARY = ROOT / "third_party/blender_human_base_meshes/v1.4.1/human-base-meshes-bundle-v1.4.1/human_base_meshes_bundle.blend"
REFERENCE_TURNAROUND = ROOT / "references/turnaround/character_turnaround_v2_face_refined.png"
REFERENCE_FACE = ROOT / "references/facial/head_expression_sheet_v2_face_refined.png"
REFERENCE_HAND = ROOT / "references/hands/m3_chord_hand_v3_compact.png"
REFERENCE_LOCK = ROOT / "references/source/approved_character_design_lock.png"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def clear_scene() -> None:
    bpy.ops.object.mode_set(mode="OBJECT") if bpy.context.object and bpy.context.object.mode != "OBJECT" else None
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for collection in list(bpy.data.collections):
        if collection.users == 0:
            bpy.data.collections.remove(collection)
    for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        for block in list(datablocks):
            if block.users == 0:
                datablocks.remove(block)


def look_at(obj: bpy.types.Object, target: Vector) -> None:
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def make_material(name: str, base_color: tuple[float, float, float, float], roughness: float) -> bpy.types.Material:
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = base_color
    bsdf.inputs["Roughness"].default_value = roughness
    return material


def make_camera(name: str, location: tuple[float, float, float], target: Vector, orthographic_scale: float) -> bpy.types.Object:
    data = bpy.data.cameras.new(name + "_DATA")
    data.type = "ORTHO"
    data.ortho_scale = orthographic_scale
    data.lens = 70.0
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = location
    look_at(obj, target)
    obj["reference_locked"] = True
    obj["lens_mm_record"] = 70.0
    return obj


def add_area_light(name: str, location: tuple[float, float, float], energy: float, size: float, target: Vector) -> None:
    data = bpy.data.lights.new(name + "_DATA", type="AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = location
    look_at(obj, target)


def add_reference_empty(name: str, path: Path, location: tuple[float, float, float], rotation: tuple[float, float, float]) -> None:
    image = bpy.data.images.load(str(path), check_existing=True)
    empty = bpy.data.objects.new(name, None)
    empty.empty_display_type = "IMAGE"
    empty.data = image
    empty.empty_display_size = 2.0
    empty.color[3] = 0.72
    empty.location = location
    empty.rotation_euler = rotation
    empty.hide_render = True
    empty["authority_path"] = "//" + str(path.relative_to(ROOT))
    bpy.context.scene.collection.objects.link(empty)


for directory in (STAGE, AUDIT_OUT.parent, RENDER_DIR):
    directory.mkdir(parents=True, exist_ok=True)

clear_scene()

with bpy.data.libraries.load(str(LIBRARY), link=False) as (source, target):
    if "Body Male - Realistic" not in source.collections:
        raise RuntimeError("Official library does not contain Body Male - Realistic")
    target.collections = ["Body Male - Realistic"]

base_collection = target.collections[0]
base_collection.name = "CHARACTER_V211_BASE"
bpy.context.scene.collection.children.link(base_collection)

body = next(obj for obj in base_collection.all_objects if obj.name == "GEO-body_male_realistic")
eye_l = next(obj for obj in base_collection.all_objects if obj.name.endswith("eye.L"))
eye_r = next(obj for obj in base_collection.all_objects if obj.name.endswith("eye.R"))
body.name = "V211_BODY_NEUTRAL"
eye_l.name = "V211_EYE_L"
eye_r.name = "V211_EYE_R"

root = bpy.data.objects.new("V211_CHARACTER_ROOT", None)
root.empty_display_type = "PLAIN_AXES"
bpy.context.scene.collection.objects.link(root)
world_height = float(body.dimensions.z)
scale_factor = 1.8 / world_height
body.parent = root
root.scale = (scale_factor, scale_factor, scale_factor)
root["scale_factor_from_official_base"] = scale_factor
bpy.context.view_layer.update()
evaluated_body = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
world_corners = [evaluated_body.matrix_world @ Vector(corner) for corner in evaluated_body.bound_box]
center_x = (min(point.x for point in world_corners) + max(point.x for point in world_corners)) * 0.5
center_y = (min(point.y for point in world_corners) + max(point.y for point in world_corners)) * 0.5
minimum_z = min(point.z for point in world_corners)
root.location = (-center_x, -center_y, -minimum_z)
bpy.context.view_layer.update()

body["source_collection"] = "Body Male - Realistic"
body["source_library"] = "//" + str(LIBRARY.relative_to(ROOT))
body["production_role"] = "neutral_body"
body["source_vertex_count"] = len(body.data.vertices)
body["source_polygon_count"] = len(body.data.polygons)

clay = make_material("MAT_V211_NEUTRAL_CLAY", (0.34, 0.24, 0.19, 1.0), 0.52)
eye = make_material("MAT_V211_EYE_REVIEW", (0.055, 0.045, 0.038, 1.0), 0.24)
body.data.materials.clear()
body.data.materials.append(clay)
for eye_obj in (eye_l, eye_r):
    eye_obj.data.materials.clear()
    eye_obj.data.materials.append(eye)

for modifier in body.modifiers:
    if modifier.type == "MULTIRES":
        modifier.levels = min(1, modifier.total_levels)
        modifier.render_levels = min(2, modifier.total_levels)
        modifier.sculpt_levels = min(1, modifier.total_levels)

target_point = Vector((0.0, 0.0, 0.92))
camera_specs = {
    "CAM_V211_FRONT": ((0.0, -4.2, 0.92), 2.08),
    "CAM_V211_BACK": ((0.0, 4.2, 0.92), 2.08),
    "CAM_V211_LEFT_PROFILE": ((-4.2, 0.0, 0.92), 2.08),
    "CAM_V211_RIGHT_PROFILE": ((4.2, 0.0, 0.92), 2.08),
    "CAM_V211_FRONT_LEFT_3Q": ((-3.0, -3.0, 0.92), 2.08),
    "CAM_V211_FRONT_RIGHT_3Q": ((3.0, -3.0, 0.92), 2.08),
}
cameras = {name: make_camera(name, location, target_point, scale) for name, (location, scale) in camera_specs.items()}

add_reference_empty("REF_V211_TURNAROUND", REFERENCE_TURNAROUND, (-2.7, 0.65, 1.0), (math.radians(90), 0.0, 0.0))
add_reference_empty("REF_V211_FACE", REFERENCE_FACE, (2.7, 0.65, 1.0), (math.radians(90), 0.0, 0.0))
add_reference_empty("REF_V211_HAND", REFERENCE_HAND, (-2.7, 0.65, -1.2), (math.radians(90), 0.0, 0.0))
add_reference_empty("REF_V211_DESIGN_LOCK", REFERENCE_LOCK, (2.7, 0.65, -1.2), (math.radians(90), 0.0, 0.0))

floor_mesh = bpy.data.meshes.new("V211_FLOOR_MESH")
floor = bpy.data.objects.new("V211_FLOOR", floor_mesh)
bpy.context.scene.collection.objects.link(floor)
floor_mesh.from_pydata([(-3, -3, 0), (3, -3, 0), (3, 3, 0), (-3, 3, 0)], [], [(0, 1, 2, 3)])
floor.data.materials.append(make_material("MAT_V211_FLOOR", (0.07, 0.08, 0.09, 1.0), 0.72))

add_area_light("KEY_V211", (-2.4, -3.0, 3.5), 950.0, 2.0, target_point)
add_area_light("FILL_V211", (2.5, -1.5, 2.2), 500.0, 2.5, target_point)
add_area_light("RIM_V211", (0.0, 2.5, 3.0), 700.0, 1.8, target_point)

scene = bpy.context.scene
scene["character_asset_stage"] = "V211_CLEAN_BASE"
scene["base_archive_sha256"] = sha256(ARCHIVE)
scene["base_library_sha256"] = sha256(LIBRARY)
scene["reference_authority"] = "supplied_design_lock_turnaround_face_hand"
scene["visual_gate"] = "alignment_pending_identity_sculpt"
scene.unit_settings.system = "METRIC"
scene.unit_settings.scale_length = 1.0
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 720
scene.render.resolution_y = 960
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGBA"
scene.render.film_transparent = False
scene.render.image_settings.color_depth = "8"
scene.world.color = (0.018, 0.022, 0.028)
scene.view_settings.look = "AgX - Medium High Contrast"

bpy.context.view_layer.update()

render_manifest: dict[str, dict[str, object]] = {}
for camera_name, camera in cameras.items():
    view_name = camera_name.removeprefix("CAM_V211_").lower()
    output = RENDER_DIR / f"{view_name}.png"
    scene.camera = camera
    scene.render.filepath = str(output)
    bpy.ops.render.render(write_still=True)
    render_manifest[view_name] = {
        "camera": camera_name,
        "path": "//" + str(output.relative_to(ROOT)),
        "sha256": sha256(output),
        "resolution": [scene.render.resolution_x, scene.render.resolution_y],
        "engine": scene.render.engine,
    }

bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_OUT), check_existing=False)
bpy.context.view_layer.update()

manifest = {
    "stage": "V211_CLEAN_BASE",
    "status": "built_visual_review_required",
    "blend": str(BLEND_OUT.relative_to(ROOT)),
    "blend_sha256": sha256(BLEND_OUT),
    "source": {
        "collection": "Body Male - Realistic",
        "archive": str(ARCHIVE.relative_to(ROOT)),
        "archive_sha256": sha256(ARCHIVE),
        "library": str(LIBRARY.relative_to(ROOT)),
        "library_sha256": sha256(LIBRARY),
        "license": "CC0-1.0",
    },
    "body": {
        "object": body.name,
        "vertices": len(body.data.vertices),
        "polygons": len(body.data.polygons),
        "world_height_m": round(float(body.dimensions.z), 6),
        "multires": [modifier.name for modifier in body.modifiers if modifier.type == "MULTIRES"],
        "uv_layers": list(body.data.uv_layers.keys()),
    },
    "references": [str(path.relative_to(ROOT)) for path in (REFERENCE_LOCK, REFERENCE_TURNAROUND, REFERENCE_FACE, REFERENCE_HAND)],
    "renders": render_manifest,
    "next_gate": "V212 neutral identity sculpt must match supplied front, profile, and three-quarter references before surfacing",
}
AUDIT_OUT.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

result = {
    "status": "V211_BUILD_OK",
    "blend": str(BLEND_OUT),
    "blend_sha256": manifest["blend_sha256"],
    "height_m": manifest["body"]["world_height_m"],
    "vertices": manifest["body"]["vertices"],
    "renders": sorted(render_manifest),
}
print("V211_BUILD_OK", result)
