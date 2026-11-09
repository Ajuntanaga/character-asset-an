from pathlib import Path
import math

import bpy
from mathutils import Vector

ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v304_fretting_rebind_probe" / "Character_An_fretting_rebind_probe_v304.blend"
RENDERS = SOURCE.parent / "renders"
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
hand = bpy.data.objects["V248_FRETTING_HAND_REALISTIC"]
rig = bpy.data.objects["V250_FRETTING_HAND_RIG"]
camera = bpy.data.objects["V287_GUITAR_CAMERA"]
for obj in bpy.context.scene.objects:
    if obj.type not in {"CAMERA", "LIGHT"} and obj != hand:
        obj.hide_render = True
hand.hide_render = False

center = sum((hand.matrix_world @ Vector(corner) for corner in hand.bound_box), Vector()) / 8.0
camera.location = center + Vector((0.0, -0.48, .06))
camera.rotation_euler = (center - camera.location).to_track_quat("-Z", "Y").to_euler()
camera.data.lens = 82.0
scene = bpy.context.scene
scene.camera = camera
scene.render.resolution_x = 1000
scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100

def render(name):
    scene.render.filepath = str(RENDERS / name)
    bpy.ops.render.render(write_still=True)

for bone in rig.pose.bones:
    bone.location = (0, 0, 0)
    bone.rotation_mode = "XYZ"
    bone.rotation_euler = (0, 0, 0)
    bone.scale = (1, 1, 1)
bpy.context.view_layer.update()
render("v304_isolated_neutral.png")
for digit in ("index", "middle", "ring", "pinky"):
    rig.pose.bones[f"{digit}_01"].rotation_euler.x = math.radians(28)
    rig.pose.bones[f"{digit}_02"].rotation_euler.x = math.radians(52)
    rig.pose.bones[f"{digit}_03"].rotation_euler.x = math.radians(34)
rig.pose.bones["thumb_01"].rotation_euler.x = math.radians(22)
rig.pose.bones["thumb_02"].rotation_euler.x = math.radians(38)
rig.pose.bones["thumb_03"].rotation_euler.x = math.radians(24)
bpy.context.view_layer.update()
render("v304_isolated_curl_x.png")
print("V304_ISOLATED_HAND_RENDER_OK")
