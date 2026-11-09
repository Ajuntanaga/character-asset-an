"""Drive current Rigify arms from the accepted V210 performance landmarks."""

from pathlib import Path
import math

import bpy
from mathutils import Euler, Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
BASE = ROOT / "production_v228_garment_rig_coupling" / "Character_An_garment_rig_v228.blend"
OUT = ROOT / "production_v230_reference_arm_pose"
RENDERS = OUT / "renders"
OUTPUT = OUT / "Character_An_reference_arm_pose_v230.blend"
RENDERS.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(BASE))

rig = bpy.data.objects["V214_CHARACTER_RIG"]
pose = rig.pose.bones


def place_control(name, target, rotation):
    bone = pose[name]
    transform = Euler(rotation, "XYZ").to_matrix().to_4x4()
    transform.translation = Vector(target)
    bone.matrix = transform


for side in ("L", "R"):
    pose[f"upper_arm_parent.{side}"]["IK_FK"] = 0.0
    pose[f"upper_arm_parent.{side}"]["IK_Stretch"] = 0.0

# Targets compensate for the current Rigify hand-control-to-DEF-hand offset and
# reproduce the accepted V210 arm landmarks instead of the rejected wide reach.
place_control("hand_ik.R", (-0.334, -0.292, 0.968), (math.radians(82), math.radians(-8), math.radians(8)))
place_control("hand_ik.L", (0.082, -0.306, 0.886), (math.radians(84), math.radians(8), math.radians(-12)))
place_control("upper_arm_ik_target.R", (-0.55, -0.12, 1.33), (0.0, 0.0, 0.0))
place_control("upper_arm_ik_target.L", (0.50, -0.12, 1.26), (0.0, 0.0, 0.0))
bpy.context.view_layer.update()

action = bpy.data.actions.get("V230_REFERENCE_ARM_POSE") or bpy.data.actions.new("V230_REFERENCE_ARM_POSE")
rig.animation_data_create()
rig.animation_data.action = action
for name in ("hand_ik.R", "hand_ik.L", "upper_arm_ik_target.R", "upper_arm_ik_target.L"):
    bone = pose[name]
    bone.keyframe_insert(data_path="location", frame=1, group=name)
    bone.keyframe_insert(data_path="rotation_euler", frame=1, group=name)
for side in ("L", "R"):
    pose[f"upper_arm_parent.{side}"].keyframe_insert(data_path='["IK_FK"]', frame=1, group=f"upper_arm_parent.{side}")

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
    "performance": (Vector((0.0, -2.55, 1.16)), Vector((-0.03, -0.02, 1.06)), 70.0, (1100, 900)),
}
for name, (location, target, lens, resolution) in views.items():
    camera.location = location
    camera.data.lens = lens
    point_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = resolution
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(RENDERS / f"v230_{name}.png")
    bpy.ops.render.render(write_still=True)

scene["V230_STATUS"] = "V210_LANDMARK_DRIVEN_RIGIFY_ARM_POSE"
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
print({
    "status": "ok",
    "output": str(OUTPUT),
    "def_hand_R": [round(v, 5) for v in pose["DEF-hand.R"].matrix.translation],
    "def_hand_L": [round(v, 5) for v in pose["DEF-hand.L"].matrix.translation],
})
