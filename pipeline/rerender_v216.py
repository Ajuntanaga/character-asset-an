from pathlib import Path

import bpy
from mathutils import Vector

root = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
out = root / "production_v216_conformed_character" / "renders"
camera = bpy.data.objects["V216_CAMERA"]
target = Vector((0.0, -0.015, 1.575))
views = {
    "front": Vector((0.0, -2.25, 1.62)),
    "left_three_quarter": Vector((-1.25, -1.75, 1.64)),
    "left_profile": Vector((-2.25, 0.0, 1.62)),
}
for name, location in views.items():
    camera.location = location
    camera.rotation_euler = (target - location).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.render.filepath = str(out / f"v216_{name}.png")
    bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
print({"status": "ok", "renders": len(views)})
