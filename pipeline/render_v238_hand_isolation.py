from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
OUTPUT = ROOT / "production_v238_continuous_fretting_hand" / "renders" / "v238_hand_isolation.png"
expected = ROOT / "production_v238_continuous_fretting_hand" / "Character_An_continuous_fretting_hand_v238.blend"
if Path(bpy.data.filepath).resolve() != expected.resolve():
    raise RuntimeError(f"Open V238 first: {expected}")

visibility = {obj.name: obj.hide_render for obj in bpy.data.objects}
try:
    for obj in bpy.data.objects:
        visible = obj.name.startswith("V206_") or obj.name == "V238_FRETTING_HAND_CONTINUOUS"
        if obj.type not in {"CAMERA", "LIGHT"}:
            obj.hide_render = not visible
    for name in ("V206_KEY", "V206_FILL", "V206_RIM"):
        if bpy.data.objects.get(name):
            bpy.data.objects[name].hide_render = True
    camera = bpy.data.objects["V232_CAMERA"]
    camera.location = Vector((-0.28, -1.08, 1.49))
    target = Vector((0.33, -0.31, 1.43))
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera.data.lens = 118.0
    scene = bpy.context.scene
    scene.camera = camera
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1200
    scene.render.resolution_y = 950
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(OUTPUT)
    bpy.ops.render.render(write_still=True)
finally:
    for name, hidden in visibility.items():
        obj = bpy.data.objects.get(name)
        if obj:
            obj.hide_render = hidden
print(f"V238_ISOLATION={OUTPUT}")
