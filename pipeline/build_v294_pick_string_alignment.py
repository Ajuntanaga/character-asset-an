"""Translate the solved dedicated pick pinch onto the bridge-side string plane."""

from pathlib import Path
import hashlib
import json

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v293_pick_pinch_solver" / "Character_An_pick_pinch_v293.blend"
STAGE = ROOT / "production_v294_pick_string_alignment"
OUTPUT = STAGE / "Character_An_pick_string_alignment_v294.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"
HUB = "V292_PICKING_HAND_HUB"
PICK = "V293_PLECTRUM"
PINCH_BEFORE = Vector((-0.0526607037, -0.4075676203, 1.1755242348))
TARGET = Vector((-0.0600, -0.3940, 1.2020))


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            digest.update(block)
    return digest.hexdigest()


def point_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(scene, camera, path, resolution):
    scene.camera = camera
    scene.render.resolution_x, scene.render.resolution_y = resolution
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(path)}


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    for folder in (STAGE, RENDERS, AUDIT):
        folder.mkdir(parents=True, exist_ok=True)
    delta = TARGET - PINCH_BEFORE
    hub = bpy.data.objects[HUB]
    hub_world = hub.matrix_world.copy()
    hub_world.translation += delta
    hub.matrix_world = hub_world
    pick = bpy.data.objects[PICK]
    pick.location += delta
    bpy.context.view_layer.update()

    scene = bpy.context.scene
    camera = bpy.data.objects["V287_GUITAR_CAMERA"]
    views = {
        "full": (Vector((0.0, -3.75, 1.02)), Vector((0.0, -0.02, 1.0)), 66.0, (900, 1000)),
        "picking_macro": (Vector((-1.22, -1.66, 1.28)), Vector((-0.10, -0.35, 1.23)), 100.0, (1200, 900)),
        "three_quarter": (Vector((-2.55, -2.75, 1.14)), Vector((0.0, -0.03, 1.02)), 70.0, (900, 1000)),
    }
    renders = {}
    for label, (location, target, lens, resolution) in views.items():
        camera.location = location
        camera.data.lens = lens
        point_at(camera, target)
        renders[label] = render(scene, camera, RENDERS / f"v294_{label}.png", resolution)
    scene["V294_STATUS"] = "PICK_PINCH_ALIGNED_TO_STRING_PLANE_REVIEW_REQUIRED"
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v294-pick-string-alignment-v1",
        "status": "VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)},
        "pinch_before_world": [float(v) for v in PINCH_BEFORE],
        "target_world": [float(v) for v in TARGET],
        "translation_world": [float(v) for v in delta],
        "renders": renders,
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha(OUTPUT)},
    }
    (AUDIT / "v294_pick_string_alignment.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V294_PICK_STRING_ALIGNMENT_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
