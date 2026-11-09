"""Visually prove authored Reom/Rigify hand weights with finger-curve controls."""

from pathlib import Path
import hashlib
import json

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v307_charmorph_reom_rig" / "Character_An_reom_rig_v307.blend"
STAGE = ROOT / "production_v308_reom_hand_deformation"
OUTPUT = STAGE / "Character_An_reom_hand_deformation_v308.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"
MASTERS = [f"f_{digit}.01_master.L" for digit in ("index", "middle", "ring", "pinky")] + ["thumb.01_master.L"]


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            digest.update(block)
    return digest.hexdigest()


def point_at(camera, target):
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()


def render(scene, camera, path, location, target):
    camera.location = location
    camera.data.lens = 92
    point_at(camera, target)
    scene.camera = camera
    scene.render.resolution_x = 1000
    scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(path)}


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    for folder in (STAGE, RENDERS, AUDIT):
        folder.mkdir(parents=True, exist_ok=True)
    body = bpy.data.objects["V307_REOM_BODY"]
    rig = bpy.data.objects["V307_REOM_RIG"]
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.image_settings.file_format = "PNG"
    if scene.world is None:
        scene.world = bpy.data.worlds.new("V308_WORLD")
    scene.world.color = (.006, .006, .009)

    camera_data = bpy.data.cameras.new("V308_HAND_CAMERA")
    camera = bpy.data.objects.new("V308_HAND_CAMERA", camera_data)
    bpy.context.collection.objects.link(camera)
    for name, location, energy, size in (
        ("KEY", (.10, -.55, 1.30), 650, .55),
        ("FILL", (.72, -.30, 1.02), 420, .45),
        ("RIM", (.40, .45, 1.15), 560, .40),
    ):
        data = bpy.data.lights.new(f"V308_{name}", "AREA")
        data.energy = energy
        data.shape = "DISK"
        data.size = size
        light = bpy.data.objects.new(f"V308_{name}", data)
        light.location = location
        point_at(light, Vector((.35, .09, .91)))
        bpy.context.collection.objects.link(light)

    target = rig.matrix_world @ Vector((.352, .090, .910))
    front = target + Vector((0, -.46, .015))
    oblique = target + Vector((.26, -.40, .12))
    for name in MASTERS:
        rig.pose.bones[name]["finger_curve"] = 0.0
    bpy.context.view_layer.update()
    renders = {
        "neutral_front": render(scene, camera, RENDERS / "v308_neutral_front.png", front, target),
    }
    for name in MASTERS:
        rig.pose.bones[name]["finger_curve"] = 1.0
    bpy.context.view_layer.update()
    renders["curve_positive_front"] = render(scene, camera, RENDERS / "v308_curve_positive_front.png", front, target)
    renders["curve_positive_oblique"] = render(scene, camera, RENDERS / "v308_curve_positive_oblique.png", oblique, target)
    for name in MASTERS:
        rig.pose.bones[name]["finger_curve"] = -1.0
    bpy.context.view_layer.update()
    renders["curve_negative_front"] = render(scene, camera, RENDERS / "v308_curve_negative_front.png", front, target)

    for name in MASTERS:
        rig.pose.bones[name]["finger_curve"] = 0.0
    bpy.context.view_layer.update()
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    ui_ranges = {
        name: rig.pose.bones[name].id_properties_ui("finger_curve").as_dict()
        for name in MASTERS
    }
    record = {
        "schema": "v308-reom-hand-deformation-v1",
        "status": "VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)},
        "controls": MASTERS,
        "property_ranges": ui_ranges,
        "renders": renders,
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha(OUTPUT)},
    }
    (AUDIT / "v308_reom_hand_deformation.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V308_REOM_HAND_DEFORMATION_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
