"""Append the validated V206 guitar into the V223 rigged-character scene."""

from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
BASE = ROOT / "production_v223_head_rig_attachment" / "Character_An_head_rig_v223.blend"
SOURCE = ROOT / "production_v206_guitar" / "ant_headless_guitar_v206.blend"
OUT = ROOT / "production_v224_guitar_integration"
RENDERS = OUT / "renders"
OUTPUT = OUT / "Character_An_guitar_integration_v224.blend"
RENDERS.mkdir(parents=True, exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=str(BASE))

for collection in list(bpy.data.collections):
    if collection.name == "V206_GUITAR_REBUILD":
        bpy.data.collections.remove(collection)

with bpy.data.libraries.load(str(SOURCE), link=False) as (data_from, data_to):
    data_to.collections = ["V206_GUITAR_REBUILD"]

guitar_collection = data_to.collections[0]
if guitar_collection.name not in {child.name for child in bpy.context.scene.collection.children}:
    bpy.context.scene.collection.children.link(guitar_collection)

guitar_objects = [obj for obj in guitar_collection.all_objects if obj.type in {"MESH", "CURVE"}]
if not guitar_objects:
    raise RuntimeError("V206 guitar collection appended without geometry")

mins = Vector((1e9, 1e9, 1e9))
maxs = Vector((-1e9, -1e9, -1e9))
for obj in guitar_objects:
    for corner in obj.bound_box:
        point = obj.matrix_world @ Vector(corner)
        mins.x = min(mins.x, point.x)
        mins.y = min(mins.y, point.y)
        mins.z = min(mins.z, point.z)
        maxs.x = max(maxs.x, point.x)
        maxs.y = max(maxs.y, point.y)
        maxs.z = max(maxs.z, point.z)

camera = bpy.data.objects["V219_CAMERA"]
camera.data.lens = 58.0


def point_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


scene = bpy.context.scene
scene.frame_set(1)
scene.camera = camera
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 900
scene.render.resolution_y = 1100
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"

views = {
    "full_front": (Vector((0.0, -4.2, 1.02)), Vector((0.0, 0.0, 0.95))),
    "guitar_contact": (Vector((0.0, -2.2, 1.23)), Vector((0.0, 0.0, 1.20))),
}
for name, (location, target) in views.items():
    camera.location = location
    point_at(camera, target)
    scene.render.filepath = str(RENDERS / f"v224_{name}.png")
    bpy.ops.render.render(write_still=True)

scene["V224_STATUS"] = "V206_GUITAR_APPENDED_FOR_CURRENT_RIG_ALIGNMENT"
scene["V224_GUITAR_BOUNDS"] = str(tuple(round(v, 5) for v in (*mins, *maxs)))
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
print({
    "status": "ok",
    "output": str(OUTPUT),
    "objects": len(guitar_objects),
    "bounds_min": [round(v, 5) for v in mins],
    "bounds_max": [round(v, 5) for v in maxs],
})
