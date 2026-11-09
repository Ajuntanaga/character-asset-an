"""Correct the 90-degree local-axis mismatch between V198 and V206 guitars."""

from pathlib import Path
import math

import bpy
from mathutils import Matrix, Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
BASE = ROOT / "production_v233_validated_guitar_hybrid" / "Character_An_validated_guitar_hybrid_v233.blend"
OUT = ROOT / "production_v234_guitar_axis_alignment"
RENDERS = OUT / "renders"
OUTPUT = OUT / "Character_An_guitar_axis_v234.blend"
RENDERS.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(BASE))

old_root = bpy.data.objects["ANTV1_GUITAR_ROOT"]
new_root = bpy.data.objects["V206_GUITAR_ROOT"]
new_root.matrix_world = old_root.matrix_world @ Matrix.Rotation(math.radians(90.0), 4, "X")

camera = bpy.data.objects["V232_CAMERA"]


def point_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


scene = bpy.context.scene
scene.frame_set(1)
scene.camera = camera
scene.render.engine = "BLENDER_EEVEE"
scene.render.image_settings.file_format = "PNG"
views = {
    "full_front": (Vector((0.0, -4.4, 1.02)), Vector((0.0, 0.0, 0.98)), 58.0, (900, 1100)),
    "performance": (Vector((0.0, -2.7, 1.18)), Vector((0.0, -0.03, 1.12)), 70.0, (1100, 900)),
}
for name, (location, target, lens, resolution) in views.items():
    camera.location = location
    camera.data.lens = lens
    point_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = resolution
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(RENDERS / f"v234_{name}.png")
    bpy.ops.render.render(write_still=True)

scene["V234_STATUS"] = "V206_GUITAR_LOCAL_AXIS_ALIGNED_TO_V198_ROOT"
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
print({"status": "ok", "output": str(OUTPUT)})
