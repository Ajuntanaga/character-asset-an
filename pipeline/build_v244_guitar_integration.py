"""Append the accepted V236 guitar transform into the V243 production character."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v243_trousers_boots" / "Character_An_trousers_boots_v243.blend"
GUITAR_SOURCE = ROOT / "production_v236_guitar_body_anchor_fit" / "Character_An_guitar_body_anchor_v236.blend"
STAGE = ROOT / "production_v244_guitar_integration"
OUTPUT = STAGE / "Character_An_guitar_integration_v244.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"
COLLECTION_NAME = "V206_GUITAR_REBUILD"
ROOT_NAME = "V206_GUITAR_ROOT"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def point_at(obj: bpy.types.Object, target: Vector) -> None:
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def main() -> None:
    if Path(bpy.data.filepath).resolve() != SOURCE.resolve():
        raise RuntimeError(f"Open V243 first: {SOURCE}")
    STAGE.mkdir(parents=True, exist_ok=True)
    RENDERS.mkdir(parents=True, exist_ok=True)
    AUDIT.mkdir(parents=True, exist_ok=True)
    existing_collection = bpy.data.collections.get(COLLECTION_NAME)
    if existing_collection and not existing_collection.all_objects:
        bpy.data.collections.remove(existing_collection)
        existing_collection = None
    if existing_collection or bpy.data.objects.get(ROOT_NAME):
        raise RuntimeError("V206 guitar already exists in the destination scene")

    with bpy.data.libraries.load(str(GUITAR_SOURCE), link=False) as (source, target):
        if COLLECTION_NAME not in source.collections:
            raise RuntimeError(f"Missing {COLLECTION_NAME} in {GUITAR_SOURCE}")
        target.collections = [COLLECTION_NAME]
    guitar_collection = target.collections[0]
    bpy.context.scene.collection.children.link(guitar_collection)
    bpy.context.view_layer.update()
    guitar_root = bpy.data.objects.get(ROOT_NAME)
    if guitar_root is None:
        raise RuntimeError(f"Appended collection lacks {ROOT_NAME}")

    hidden = []
    for name in ("V206_KEY", "V206_FILL", "V206_RIM"):
        obj = bpy.data.objects.get(name)
        if obj:
            obj.hide_render = True
            obj.hide_viewport = True
            hidden.append(name)
    guitar_root["v244_transform_authority"] = "V236_BODY_CENTER_ANCHORED"
    guitar_root["v244_scale_authority"] = 0.92

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.look = "AgX - Medium High Contrast"
    camera = bpy.data.objects["CAM_V211_FRONT"]
    camera.data.type = "PERSP"
    views = {
        "front": (Vector((0.0, -3.75, 1.00)), Vector((0.0, 0.0, 0.98)), 66.0, (900, 1000)),
        "three_quarter": (Vector((-2.65, -2.75, 1.10)), Vector((0.0, 0.0, 1.00)), 70.0, (900, 1000)),
        "instrument": (Vector((-1.45, -2.35, 1.02)), Vector((0.0, 0.0, 0.98)), 78.0, (1100, 850)),
    }
    render_records = {}
    for label, (location, target_point, lens, resolution) in views.items():
        camera.location = location
        camera.data.lens = lens
        point_at(camera, target_point)
        scene.camera = camera
        scene.render.resolution_x, scene.render.resolution_y = resolution
        scene.render.resolution_percentage = 100
        path = RENDERS / f"v244_{label}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        render_records[label] = {"path": str(path.relative_to(ROOT)), "sha256": sha256(path)}

    matrix = [[float(value) for value in row] for row in guitar_root.matrix_world]
    objects = list(guitar_collection.all_objects)
    scene["V244_STATUS"] = "V236_ACCEPTED_GUITAR_TRANSFORM_APPENDED"
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v244-guitar-integration-v1",
        "status": "BUILT_VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha256(SOURCE)},
        "guitar_source": {"path": str(GUITAR_SOURCE.relative_to(ROOT)), "sha256": sha256(GUITAR_SOURCE)},
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha256(OUTPUT)},
        "collection": COLLECTION_NAME,
        "object_count": len(objects),
        "root": ROOT_NAME,
        "root_matrix_world": matrix,
        "hidden_product_lights": hidden,
        "renders": render_records,
    }
    (AUDIT / "v244_manifest.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("V244_GUITAR_INTEGRATION_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
