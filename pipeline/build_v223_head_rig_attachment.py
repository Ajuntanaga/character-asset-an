"""Attach the accepted V221 head assembly to Rigify without changing world transforms."""

from pathlib import Path
import math

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
OUT = ROOT / "production_v223_head_rig_attachment"
RENDERS = OUT / "renders" / "deformation"
OUTPUT = OUT / "Character_An_head_rig_v223.blend"
RENDERS.mkdir(parents=True, exist_ok=True)

rig = bpy.data.objects["V214_CHARACTER_RIG"]
head_bone = rig.pose.bones["head"]

assembly_names = [
    "V216_REFERENCE_FITTED_HEAD",
    "V216_EYE_L", "V216_EYE_R",
    "V216_IRIS_L", "V216_IRIS_R",
    "V216_PUPIL_L", "V216_PUPIL_R",
    "V217_TIGHT_CURL_GROOM", "V217_CURL_CLUSTERS",
    "V217_BROWS", "V217_BEARD_STUBBLE",
]

attached = []
for name in assembly_names:
    obj = bpy.data.objects.get(name)
    if obj is None:
        continue
    world = obj.matrix_world.copy()
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = "head"
    obj.matrix_world = world
    attached.append(obj.name)

# Keep the V221 visibility verdicts.
for name in ("V217_BROWS", "V217_BEARD_STUBBLE"):
    obj = bpy.data.objects.get(name)
    if obj:
        obj.hide_render = True
        obj.hide_viewport = True

# Head-control action: neutral, readable left/right yaw, then neutral.
bpy.context.view_layer.objects.active = rig
rig.select_set(True)
bpy.ops.object.mode_set(mode="POSE")
head_bone.rotation_mode = "XYZ"
action = bpy.data.actions.get("V223_HEAD_TURN_TEST") or bpy.data.actions.new("V223_HEAD_TURN_TEST")
rig.animation_data_create()
rig.animation_data.action = action
for frame, yaw in ((1, 0.0), (12, math.radians(-18.0)), (24, math.radians(18.0)), (36, 0.0)):
    head_bone.rotation_euler = (0.0, yaw, 0.0)
    head_bone.keyframe_insert(data_path="rotation_euler", frame=frame, group="head")
bpy.ops.object.mode_set(mode="OBJECT")

camera = bpy.data.objects["V219_CAMERA"]
camera.data.lens = 78.0
camera.location = Vector((0.0, -1.42, 1.61))
target = Vector((0.0, -0.01, 1.59))
camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()

scene = bpy.context.scene
scene.camera = camera
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 900
scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"

for frame, label in ((1, "neutral"), (12, "turn_left"), (24, "turn_right")):
    scene.frame_set(frame)
    scene.render.filepath = str(RENDERS / f"v223_{label}.png")
    bpy.ops.render.render(write_still=True)

scene.frame_set(1)
scene["V223_STATUS"] = "HEAD_ASSEMBLY_ATTACHED_WITH_DEFORMATION_TEST"
scene["V223_ATTACHED_OBJECTS"] = ",".join(attached)
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
print({"status": "ok", "output": str(OUTPUT), "attached": attached, "action": action.name})
