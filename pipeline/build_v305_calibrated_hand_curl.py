"""Validate the rebind using the measured local-Z flexion axes."""

from pathlib import Path
import hashlib
import json
import math

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v304_fretting_rebind_probe" / "Character_An_fretting_rebind_probe_v304.blend"
STAGE = ROOT / "production_v305_calibrated_hand_curl"
OUTPUT = STAGE / "Character_An_calibrated_hand_curl_v305.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            digest.update(block)
    return digest.hexdigest()


def point_at(camera, target):
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()


def render(scene, camera, path, location, target, lens=78):
    camera.location = location
    camera.data.lens = lens
    point_at(camera, target)
    scene.camera = camera
    scene.render.resolution_x = 1000
    scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(path)}


def reset_pose(rig):
    for bone in rig.pose.bones:
        bone.location = (0, 0, 0)
        bone.rotation_mode = "XYZ"
        bone.rotation_euler = (0, 0, 0)
        bone.scale = (1, 1, 1)
    bpy.context.view_layer.update()


def curl_pose(rig):
    values = {
        "index": (30, 58, 38),
        "middle": (34, 62, 40),
        "ring": (38, 66, 42),
        "pinky": (42, 70, 44),
        "thumb": (18, 35, 22),
    }
    for digit, angles in values.items():
        for joint, angle in enumerate(angles, 1):
            rig.pose.bones[f"{digit}_{joint:02d}"].rotation_euler.z = math.radians(angle)
    bpy.context.view_layer.update()
    return values


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    for folder in (STAGE, RENDERS, AUDIT):
        folder.mkdir(parents=True, exist_ok=True)
    hand = bpy.data.objects["V248_FRETTING_HAND_REALISTIC"]
    rig = bpy.data.objects["V250_FRETTING_HAND_RIG"]
    camera = bpy.data.objects["V287_GUITAR_CAMERA"]
    scene = bpy.context.scene
    visibility = {obj.name: obj.hide_render for obj in scene.objects}
    for obj in scene.objects:
        if obj.type not in {"LIGHT", "CAMERA"} and obj != hand:
            obj.hide_render = True
    hand.hide_render = False
    center = sum((hand.matrix_world @ Vector(corner) for corner in hand.bound_box), Vector()) / 8.0
    local = rig.matrix_world.to_3x3()
    front = center + local @ Vector((.43, 0.0, .03))
    side = center + local @ Vector((.03, -.43, .02))
    renders = {}
    reset_pose(rig)
    renders["neutral_front"] = render(scene, camera, RENDERS / "v305_neutral_front.png", front, center)
    angles = curl_pose(rig)
    renders["curl_front"] = render(scene, camera, RENDERS / "v305_curl_front.png", front, center)
    renders["curl_side"] = render(scene, camera, RENDERS / "v305_curl_side.png", side, center)
    for obj in scene.objects:
        if obj.name in visibility:
            obj.hide_render = visibility[obj.name]
    hand.hide_render = False
    bpy.context.view_layer.update()
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v305-calibrated-hand-curl-v1",
        "status": "VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)},
        "flexion_axis": "local_z_positive",
        "angles_degrees": angles,
        "renders": renders,
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha(OUTPUT)},
    }
    (AUDIT / "v305_calibrated_hand_curl.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V305_CALIBRATED_HAND_CURL_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
