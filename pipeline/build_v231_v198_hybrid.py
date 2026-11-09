"""Evaluate the current FaceBuilder identity on the proven V197/V198 performance rig."""

from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
BASE = ROOT / "production_v198_deformation" / "ant_deformation_ready_v198.blend"
HEAD_SOURCE = ROOT / "production_v221_identity_cleanup" / "Character_An_identity_cleanup_v221.blend"
OUT = ROOT / "production_v232_v198_hybrid_world_head"
RENDERS = OUT / "renders"
OUTPUT = OUT / "Character_An_v198_hybrid_v232.blend"
RENDERS.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(BASE))

assembly_names = [
    "V216_REFERENCE_FITTED_HEAD",
    "V216_EYE_L", "V216_EYE_R",
    "V216_IRIS_L", "V216_IRIS_R",
    "V216_PUPIL_L", "V216_PUPIL_R",
    "V217_TIGHT_CURL_GROOM", "V217_CURL_CLUSTERS",
    "V217_BROWS", "V217_BEARD_STUBBLE",
]
with bpy.data.libraries.load(str(HEAD_SOURCE), link=False) as (data_from, data_to):
    data_to.objects = [name for name in assembly_names if name in data_from.objects]

for obj in data_to.objects:
    if obj is not None:
        bpy.context.scene.collection.objects.link(obj)

rig = bpy.data.objects["V197_RIG"]

for name in ("V217_BROWS", "V217_BEARD_STUBBLE"):
    obj = bpy.data.objects.get(name)
    if obj:
        obj.hide_render = True
        obj.hide_viewport = True

old_head = bpy.data.objects.get("V194_HEAD")
if old_head:
    old_head.hide_render = True
    old_head.hide_viewport = True
old_hair_collection = bpy.data.collections.get("V92_CONTINUOUS_CURLY_HAIR_COLLECTION")
if old_hair_collection:
    for obj in old_hair_collection.all_objects:
        obj.hide_render = True
        obj.hide_viewport = True

action = bpy.data.actions.get("V197_PERFORMANCE_POSE")
rig.animation_data_create()
rig.animation_data.action = action

camera_data = bpy.data.cameras.new("V232_CAMERA_DATA")
camera_data.lens = 62.0
camera = bpy.data.objects.new("V232_CAMERA", camera_data)
bpy.context.scene.collection.objects.link(camera)


def point_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


for name, location, energy, size in (
    ("KEY", (-2.8, -3.8, 3.8), 1100.0, 4.0),
    ("FILL", (2.8, -2.4, 2.2), 480.0, 3.5),
    ("RIM", (2.0, 2.8, 3.2), 720.0, 3.0),
):
    data = bpy.data.lights.new(f"V232_{name}_DATA", "AREA")
    data.energy = energy
    data.size = size
    light = bpy.data.objects.new(f"V232_{name}", data)
    bpy.context.scene.collection.objects.link(light)
    light.location = location
    point_at(light, Vector((0.0, 0.0, 1.05)))

scene = bpy.context.scene
scene.frame_set(1)
scene.camera = camera
scene.render.engine = "BLENDER_EEVEE"
scene.render.image_settings.file_format = "PNG"
scene.world.color = (0.018, 0.018, 0.018)
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
    scene.render.filepath = str(RENDERS / f"v232_{name}.png")
    bpy.ops.render.render(write_still=True)

scene["V232_STATUS"] = "CURRENT_IDENTITY_WORLD_ALIGNED_WITH_V198_PERFORMANCE_RIG_CANDIDATE"
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
print({"status": "ok", "output": str(OUTPUT), "action": action.name if action else None})
