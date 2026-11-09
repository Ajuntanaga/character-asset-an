"""Integrate the validated V205 garment shells with the V217 identity base."""

from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v205_wardrobe" / "ant_wardrobe_boots_v205.blend"
STAGE = ROOT / "production_v218_wardrobe_integration"
OUTPUT = STAGE / "Character_An_wardrobe_v218.blend"
RENDER_DIR = STAGE / "renders"
STAGE.mkdir(parents=True, exist_ok=True)
RENDER_DIR.mkdir(parents=True, exist_ok=True)

for obj in list(bpy.data.objects):
    if obj.name.startswith("V218_") or obj.get("v218_imported"):
        bpy.data.objects.remove(obj, do_unlink=True)

exact = {
    "V205_FITTED_TROUSERS_SHELL", "V205_TROUSER_WAISTBAND",
    "V205_TROUSER_CUFF_R", "V205_TROUSER_CUFF_L",
    "V205_TROUSER_CREASE_R", "V205_TROUSER_CREASE_L",
    "V205_FITTED_SHIRT_SHELL", "V205_SHIRT_PLACKET",
    "V205_SHIRT_COLLAR_R", "V205_SHIRT_COLLAR_L",
    "V205_FITTED_JACKET_SHELL", "V205_JACKET_LAPEL_R",
    "V205_JACKET_LAPEL_L", "V205_JACKET_POCKET_R",
    "V205_JACKET_POCKET_L", "V205_JACKET_POCKET_FLAP_R",
    "V205_JACKET_POCKET_FLAP_L", "V205_JACKET_POCKET_SEAM_R",
    "V205_JACKET_POCKET_SEAM_L", "V205_JACKET_HEM_STITCH",
    "V205_JACKET_FRONT_STITCH_R", "V205_JACKET_FRONT_STITCH_L",
    "V205_JACKET_CUFF_R", "V205_JACKET_CUFF_L", "V205_PEN",
    "V205_FITTED_BOOT_R", "V205_FITTED_BOOT_L",
    "V205_BOOT_TOE_R", "V205_BOOT_TOE_L", "V205_BOOT_SOLE_R",
    "V205_BOOT_SOLE_L", "V205_BOOT_WELT_R", "V205_BOOT_WELT_L",
    "V205_BOOT_HEEL_R", "V205_BOOT_HEEL_L",
    "V205_BOOT_FITTED_SHAFT_R", "V205_BOOT_FITTED_SHAFT_L",
    "V205_BOOT_FITTED_GORE_R", "V205_BOOT_FITTED_GORE_L",
    "V205_BOOT_PULL_TAB_R", "V205_BOOT_PULL_TAB_L",
}
exact.update({f"V205_SHIRT_BUTTON_{index:02d}" for index in range(1, 8)})

with bpy.data.libraries.load(str(SOURCE), link=False) as (data_from, data_to):
    data_to.objects = [name for name in data_from.objects if name in exact]

collection = bpy.data.collections.get("V218_WARDROBE") or bpy.data.collections.new("V218_WARDROBE")
if collection.name not in bpy.context.scene.collection.children:
    bpy.context.scene.collection.children.link(collection)
imported = []
for obj in data_to.objects:
    if obj is None:
        continue
    if not obj.users_collection:
        collection.objects.link(obj)
    elif collection not in obj.users_collection:
        collection.objects.link(obj)
    obj["v218_imported"] = True
    obj.hide_render = False
    imported.append(obj)

# Favor physically plausible rough cloth/leather responses over the old glossy previews.
for material in bpy.data.materials:
    if not material.name.startswith("MAT_V205_") or not material.use_nodes:
        continue
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if not bsdf:
        continue
    if "BOOT" in material.name:
        bsdf.inputs["Roughness"].default_value = 0.34
    elif "JACKET" in material.name or "TROUSER" in material.name:
        bsdf.inputs["Roughness"].default_value = 0.68
    else:
        bsdf.inputs["Roughness"].default_value = 0.58

# Use a dedicated full-body camera and broad studio lights.
camera_data = bpy.data.cameras.new("V218_CAMERA_DATA")
camera_data.lens = 72.0
camera = bpy.data.objects.new("V218_CAMERA", camera_data)
bpy.context.scene.collection.objects.link(camera)
camera.hide_render = False


def point_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


target = Vector((0.0, 0.0, 0.93))
for name, location, energy, size in (
    ("KEY", (-2.8, -3.8, 3.8), 1050.0, 4.0),
    ("FILL", (2.8, -2.4, 2.2), 520.0, 3.5),
    ("RIM", (2.0, 2.8, 3.2), 800.0, 3.0),
):
    data = bpy.data.lights.new(f"V218_{name}_DATA", "AREA")
    data.energy = energy
    data.size = size
    obj = bpy.data.objects.new(f"V218_{name}", data)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = location
    point_at(obj, target)
    obj.hide_render = False

scene = bpy.context.scene
scene.camera = camera
scene.frame_set(1)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 720
scene.render.resolution_y = 960
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.world.color = (0.018, 0.018, 0.018)
views = {
    "front": Vector((0.0, -4.15, 1.0)),
    "left_three_quarter": Vector((-2.7, -3.15, 1.05)),
    "left_profile": Vector((-4.15, 0.0, 1.0)),
}
for name, location in views.items():
    camera.location = location
    point_at(camera, target)
    scene.render.filepath = str(RENDER_DIR / f"v218_{name}.png")
    bpy.ops.render.render(write_still=True)

scene["V218_STATUS"] = "WARDROBE_INTEGRATION_VISUAL_CANDIDATE"
scene["V218_IMPORTED_OBJECTS"] = len(imported)
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
print({"status": "ok", "output": str(OUTPUT), "imported": len(imported)})
