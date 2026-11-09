"""Correct the Rigify IK/FK blend convention used in V226."""

from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
BASE = ROOT / "production_v226_arm_performance_pose" / "Character_An_arm_performance_v226.blend"
OUT = ROOT / "production_v227_ik_correction"
RENDERS = OUT / "renders"
OUTPUT = OUT / "Character_An_arm_performance_v227.blend"
RENDERS.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(BASE))

rig = bpy.data.objects["V214_CHARACTER_RIG"]
for side in ("L", "R"):
    control = rig.pose.bones[f"upper_arm_parent.{side}"]
    control["IK_FK"] = 0.0
    control.keyframe_insert(data_path='["IK_FK"]', frame=1, group=f"upper_arm_parent.{side}")

bpy.context.view_layer.update()

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
    scene.render.filepath = str(RENDERS / f"v227_{name}.png")
    bpy.ops.render.render(write_still=True)

scene["V227_STATUS"] = "RIGIFY_IK_BLEND_CORRECTED"
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
print({
    "status": "ok",
    "output": str(OUTPUT),
    "def_hand_R": [round(v, 5) for v in rig.pose.bones["DEF-hand.R"].matrix.translation],
    "def_hand_L": [round(v, 5) for v in rig.pose.bones["DEF-hand.L"].matrix.translation],
})
