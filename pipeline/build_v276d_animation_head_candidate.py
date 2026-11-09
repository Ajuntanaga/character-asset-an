"""Append and visually inspect Blender's official animation-ready head."""

from pathlib import Path
import hashlib
import json

import bpy
from mathutils import Matrix, Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v270_boot_finish_cuffs" / "Character_An_boot_finish_cuffs_v270.blend"
LIBRARY = ROOT / "third_party/blender_human_base_meshes/v1.4.1/human-base-meshes-bundle-v1.4.1/human_base_meshes_bundle.blend"
STAGE = ROOT / "production_v276d_animation_head_candidate"
OUTPUT = STAGE / "Character_An_animation_head_candidate_v276d.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"
TARGET = "V216_REFERENCE_FITTED_HEAD"


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def bounds(objects):
    points = [obj.matrix_world @ Vector(corner) for obj in objects for corner in obj.bound_box]
    low = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
    high = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
    return low, high


def point_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def main():
    if Path(bpy.data.filepath).resolve() != SOURCE.resolve():
        raise RuntimeError(f"Open V270 first: {SOURCE}")
    STAGE.mkdir(parents=True, exist_ok=True)
    RENDERS.mkdir(parents=True, exist_ok=True)
    AUDIT.mkdir(parents=True, exist_ok=True)
    before = set(bpy.data.objects)
    with bpy.data.libraries.load(str(LIBRARY), link=False) as (data_from, data_to):
        wanted = [name for name in ("Head (Animation) - Realistic", "Jaw - Realistic") if name in data_from.collections]
        data_to.collections = wanted
    appended_collections = [collection for collection in data_to.collections if collection is not None]
    for collection in appended_collections:
        if collection.name not in bpy.context.scene.collection.children:
            bpy.context.scene.collection.children.link(collection)
    appended = [obj for obj in bpy.data.objects if obj not in before]
    meshes = [obj for obj in appended if obj.type == "MESH"]
    head = next((obj for obj in meshes if obj.name.startswith("GEO-head_animation_realistic") and ".iris" not in obj.name and ".sclera" not in obj.name), None)
    if head is None:
        raise RuntimeError(f"Animation head mesh missing; appended {[obj.name for obj in appended]}")
    target = bpy.data.objects[TARGET]
    source_low, source_high = bounds([head])
    target_low, target_high = bounds([target])
    source_center = (source_low + source_high) * 0.5
    target_center = (target_low + target_high) * 0.5
    scale = (target_high.z - target_low.z) / (source_high.z - source_low.z)
    transfer = Matrix.Translation(target_center) @ Matrix.Scale(scale, 4) @ Matrix.Translation(-source_center)
    for obj in appended:
        obj.matrix_world = transfer @ obj.matrix_world
        obj.name = f"V276D_{obj.name}"

    candidate_set = set(appended)
    for obj in bpy.context.scene.objects:
        obj.hide_render = obj not in candidate_set
    target.hide_render = True

    camera_data = bpy.data.cameras.new("V276D_CAMERA_DATA")
    camera = bpy.data.objects.new("V276D_CAMERA", camera_data)
    bpy.context.scene.collection.objects.link(camera)
    camera.hide_render = False
    camera.data.lens = 92
    key_data = bpy.data.lights.new("V276D_KEY_DATA", "AREA")
    key_data.energy, key_data.size = 650, 1.8
    key = bpy.data.objects.new("V276D_KEY", key_data)
    bpy.context.scene.collection.objects.link(key)
    key.location = (-1.2, -1.8, 2.5)
    point_at(key, target_center)
    key.hide_render = False
    fill_data = bpy.data.lights.new("V276D_FILL_DATA", "AREA")
    fill_data.energy, fill_data.size = 280, 1.5
    fill = bpy.data.objects.new("V276D_FILL", fill_data)
    bpy.context.scene.collection.objects.link(fill)
    fill.location = (1.0, -1.4, 1.9)
    point_at(fill, target_center)
    fill.hide_render = False

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 768
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.world.color = (0.01, 0.01, 0.01)
    views = {
        "front": (Vector((0.0, -2.05, target_center.z)), target_center),
        "three_quarter": (Vector((-1.15, -1.72, target_center.z + 0.02)), target_center),
        "profile": (Vector((-2.05, 0.0, target_center.z)), target_center),
    }
    render_paths = []
    for label, (location, look) in views.items():
        camera.location = location
        point_at(camera, look)
        scene.camera = camera
        path = RENDERS / f"v276d_{label}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        render_paths.append(str(path.relative_to(ROOT)))

    mesh_records = []
    for obj in meshes:
        data = obj.data
        mesh_records.append({
            "object": obj.name,
            "vertices": len(data.vertices),
            "edges": len(data.edges),
            "polygons": len(data.polygons),
            "uv_layers": [layer.name for layer in data.uv_layers],
            "materials": [slot.material.name if slot.material else None for slot in obj.material_slots],
            "shape_keys": [key.name for key in data.shape_keys.key_blocks] if data.shape_keys else [],
        })
    scene["V276D_STATUS"] = "OFFICIAL_ANIMATION_HEAD_CANDIDATE_VISUAL_REVIEW_REQUIRED"
    scene["V276D_ALIGNMENT_SCALE"] = scale
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v276d-animation-head-candidate-v1",
        "status": "BUILT_VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha256(SOURCE)},
        "library": {"path": str(LIBRARY.relative_to(ROOT)), "sha256": sha256(LIBRARY)},
        "collections": [collection.name for collection in appended_collections],
        "alignment_scale": scale,
        "source_bounds": [list(source_low), list(source_high)],
        "target_bounds": [list(target_low), list(target_high)],
        "meshes": mesh_records,
        "renders": render_paths,
        "output": {"path": str(OUTPUT.relative_to(ROOT))},
    }
    record["output"]["sha256"] = sha256(OUTPUT)
    (AUDIT / "v276d_animation_head_candidate.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V276D_ANIMATION_HEAD_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
