"""Place the validated V206 guitar at a believable final playing transform."""

from pathlib import Path
import math

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
BASE = ROOT / "production_v224_guitar_integration" / "Character_An_guitar_integration_v224.blend"
OUT = ROOT / "production_v225_playing_position"
RENDERS = OUT / "renders"
OUTPUT = OUT / "Character_An_playing_position_v225.blend"
RENDERS.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(BASE))

root = bpy.data.objects["V206_GUITAR_ROOT"]
root.location = (-0.50, -0.22, 0.76)
root.rotation_mode = "XYZ"
root.rotation_euler = (math.radians(90.0), math.radians(-18.0), math.radians(-2.0))
root.scale = (0.88, 0.88, 0.88)

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
    "instrument_torso": (Vector((0.0, -2.35, 1.12)), Vector((0.0, 0.0, 1.02)), 72.0, (1000, 900)),
}
for name, (location, target, lens, resolution) in views.items():
    camera.location = location
    camera.data.lens = lens
    point_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = resolution
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(RENDERS / f"v225_{name}.png")
    bpy.ops.render.render(write_still=True)

scene["V225_STATUS"] = "GUITAR_FINAL_TRANSFORM_CANDIDATE_FOR_HAND_SOLVE"
scene["V225_GUITAR_TRANSFORM"] = str((tuple(root.location), tuple(root.rotation_euler), tuple(root.scale)))
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
print({"status": "ok", "output": str(OUTPUT), "location": list(root.location), "rotation": list(root.rotation_euler), "scale": list(root.scale)})
