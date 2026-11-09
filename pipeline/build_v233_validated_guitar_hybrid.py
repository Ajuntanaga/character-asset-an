"""Replace the V198 blockout guitar with the validated V206 rebuild at the proven root."""

from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
BASE = ROOT / "production_v232_v198_hybrid_world_head" / "Character_An_v198_hybrid_v232.blend"
GUITAR_SOURCE = ROOT / "production_v206_guitar" / "ant_headless_guitar_v206.blend"
OUT = ROOT / "production_v233_validated_guitar_hybrid"
RENDERS = OUT / "renders"
OUTPUT = OUT / "Character_An_validated_guitar_hybrid_v233.blend"
RENDERS.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(BASE))

old_root = bpy.data.objects["ANTV1_GUITAR_ROOT"]
target_matrix = old_root.matrix_world.copy()

with bpy.data.libraries.load(str(GUITAR_SOURCE), link=False) as (data_from, data_to):
    data_to.collections = ["V206_GUITAR_REBUILD"]
collection = data_to.collections[0]
bpy.context.scene.collection.children.link(collection)

new_root = bpy.data.objects["V206_GUITAR_ROOT"]
new_root.matrix_world = target_matrix

old_root.hide_render = True
old_root.hide_viewport = True
for obj in old_root.children_recursive:
    obj.hide_render = True
    obj.hide_viewport = True

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
    "fretting": (Vector((-0.95, -1.75, 1.34)), Vector((-0.30, -0.20, 1.34)), 88.0, (1000, 900)),
}
for name, (location, target, lens, resolution) in views.items():
    camera.location = location
    camera.data.lens = lens
    point_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = resolution
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(RENDERS / f"v233_{name}.png")
    bpy.ops.render.render(write_still=True)

scene["V233_STATUS"] = "CURRENT_IDENTITY_PROVEN_RIG_VALIDATED_V206_GUITAR"
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
print({"status": "ok", "output": str(OUTPUT), "new_root_matrix": [[round(value, 5) for value in row] for row in new_root.matrix_world]})
