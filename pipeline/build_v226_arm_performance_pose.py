"""Create the first current-rig two-arm guitar performance pose using Rigify IK."""

from pathlib import Path
import math

import bpy
from mathutils import Euler, Matrix, Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
BASE = ROOT / "production_v225_playing_position" / "Character_An_playing_position_v225.blend"
OUT = ROOT / "production_v226_arm_performance_pose"
RENDERS = OUT / "renders"
OUTPUT = OUT / "Character_An_arm_performance_v226.blend"
RENDERS.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(BASE))

rig = bpy.data.objects["V214_CHARACTER_RIG"]
pose = rig.pose.bones

for side in ("L", "R"):
    pose[f"upper_arm_parent.{side}"]["IK_FK"] = 1.0
    pose[f"upper_arm_parent.{side}"]["IK_Stretch"] = 0.05


def place_control(name, target, rotation):
    bone = pose[name]
    transform = Euler(rotation, "XYZ").to_matrix().to_4x4()
    transform.translation = Vector(target)
    bone.matrix = transform


# Screen-left/right correspond to character R/L in the front-facing shot.
place_control("hand_ik.R", (-0.55, -0.235, 1.04), (math.radians(80), math.radians(-8), math.radians(12)))
place_control("hand_ik.L", (0.16, -0.255, 0.93), (math.radians(82), math.radians(8), math.radians(-18)))
place_control("upper_arm_ik_target.R", (-0.48, 0.12, 1.17), (0.0, 0.0, 0.0))
place_control("upper_arm_ik_target.L", (0.46, 0.10, 1.14), (0.0, 0.0, 0.0))

action = bpy.data.actions.get("V226_GUITAR_ARM_POSE") or bpy.data.actions.new("V226_GUITAR_ARM_POSE")
rig.animation_data_create()
rig.animation_data.action = action
for bone_name in ("hand_ik.R", "hand_ik.L", "upper_arm_ik_target.R", "upper_arm_ik_target.L"):
    bone = pose[bone_name]
    bone.keyframe_insert(data_path="location", frame=1, group=bone_name)
    bone.keyframe_insert(data_path="rotation_euler", frame=1, group=bone_name)

camera = bpy.data.objects["V219_CAMERA"]


def point_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


scene = bpy.context.scene
scene.frame_set(1)
scene.camera = camera
scene.render.engine = "BLENDER_EEVEE"
scene.render.image_settings.file_format = "PNG"
views = {
    "full_front": (Vector((0.0, -4.2, 1.02)), Vector((0.0, 0.0, 0.95)), 58.0, (900, 1100)),
    "performance": (Vector((0.0, -2.55, 1.16)), Vector((-0.05, -0.02, 1.06)), 70.0, (1100, 900)),
}
for name, (location, target, lens, resolution) in views.items():
    camera.location = location
    camera.data.lens = lens
    point_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = resolution
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(RENDERS / f"v226_{name}.png")
    bpy.ops.render.render(write_still=True)

scene["V226_STATUS"] = "TWO_ARM_IK_GUITAR_POSE_CANDIDATE"
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
print({"status": "ok", "output": str(OUTPUT), "action": action.name})
