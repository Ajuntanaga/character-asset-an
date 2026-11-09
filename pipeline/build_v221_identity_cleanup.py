"""Correct the most visible V220 identity failures and render a clean candidate."""

from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
OUT = ROOT / "production_v221_identity_cleanup"
RENDERS = OUT / "renders"
OUTPUT = OUT / "Character_An_identity_cleanup_v221.blend"
RENDERS.mkdir(parents=True, exist_ok=True)

# The baked reference already carries brows and beard. The old strand overlays read as
# duplicate stitches/needles, so retain them in-file but remove them from rendering.
for name in ("V217_BROWS", "V217_BEARD_STUBBLE"):
    obj = bpy.data.objects.get(name)
    if obj:
        obj.hide_render = True
        obj.hide_viewport = True

# Align the procedural eyeballs to the solved eye landmarks. The prior centers were
# 22 mm too low and exposed too much sclera.
for side in ("L", "R"):
    marker = bpy.data.objects[f"LM_V212_EYE_{side}"]
    eye = bpy.data.objects[f"V216_EYE_{side}"]
    iris = bpy.data.objects[f"V216_IRIS_{side}"]
    pupil = bpy.data.objects[f"V216_PUPIL_{side}"]
    center = marker.location.copy()
    eye.location = center
    eye.scale *= 0.90
    iris.location.x = center.x
    iris.location.y = center.y - 0.01155
    iris.location.z = center.z
    iris.scale *= 0.88
    pupil.location.x = center.x
    pupil.location.y = center.y - 0.0119
    pupil.location.z = center.z
    pupil.scale *= 0.82

# Reduce the wiry halo without discarding the authored groom.
for name in ("V217_HAIR_CURLS", "V217_HAIR_CLUSTERS"):
    obj = bpy.data.objects.get(name)
    if obj and obj.type == "CURVE":
        obj.data.bevel_depth *= 0.70
        obj.data.bevel_resolution = max(obj.data.bevel_resolution, 2)

camera = bpy.data.objects["V219_CAMERA"]
camera.data.lens = 92.0


def point_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


scene = bpy.context.scene
scene.camera = camera
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 900
scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
target = Vector((0.0, -0.01, 1.61))
views = {
    "front": Vector((0.0, -1.14, 1.61)),
    "left_three_quarter": Vector((-0.72, -0.78, 1.63)),
    "left_profile": Vector((-1.14, 0.0, 1.61)),
}
for name, location in views.items():
    camera.location = location
    point_at(camera, target)
    scene.render.filepath = str(RENDERS / f"v221_{name}.png")
    bpy.ops.render.render(write_still=True)

scene["V221_STATUS"] = "IDENTITY_CLEANUP_CANDIDATE"
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
print({"status": "ok", "output": str(OUTPUT), "renders": [str(RENDERS / f"v221_{name}.png") for name in views]})
