"""Make all body-derived V219 garments follow the existing deform rig."""

from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
BASE = ROOT / "production_v227_ik_correction" / "Character_An_arm_performance_v227.blend"
OUT = ROOT / "production_v228_garment_rig_coupling"
RENDERS = OUT / "renders"
OUTPUT = OUT / "Character_An_garment_rig_v228.blend"
RENDERS.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(BASE))

rig = bpy.data.objects["V214_CHARACTER_RIG"]
garment_names = (
    "V219_FITTED_SHIRT",
    "V219_OPEN_JACKET",
    "V219_TAPERED_TROUSERS",
    "V219_FITTED_BOOT_UPPERS",
    "V219_FITTED_BOOT_SOLES",
)
coupled = []
for name in garment_names:
    obj = bpy.data.objects[name]
    modifier = obj.modifiers.get("V228_ARMATURE") or obj.modifiers.new("V228_ARMATURE", "ARMATURE")
    modifier.object = rig
    modifier.use_deform_preserve_volume = True
    obj.modifiers.move(obj.modifiers.find(modifier.name), 0)
    coupled.append(name)

# Rigid shirt/jacket details follow the upper torso control as one assembly.
for obj in bpy.data.objects:
    if obj.name.startswith(("V219_SHIRT_BUTTON_", "V219_SHIRT_COLLAR_", "V219_JACKET_LAPEL_", "V219_JACKET_POCKET_")) or obj.name == "V219_SHIRT_PLACKET":
        world = obj.matrix_world.copy()
        obj.parent = rig
        obj.parent_type = "BONE"
        obj.parent_bone = "chest"
        obj.matrix_world = world

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
    scene.render.filepath = str(RENDERS / f"v228_{name}.png")
    bpy.ops.render.render(write_still=True)

scene["V228_STATUS"] = "BODY_DERIVED_GARMENTS_ARMATURE_COUPLED"
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
print({"status": "ok", "output": str(OUTPUT), "coupled": coupled})
