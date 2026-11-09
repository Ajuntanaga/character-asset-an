from pathlib import Path
import bpy
from mathutils import Matrix, Vector

root = Path(__file__).resolve().parents[1]
scene = bpy.context.scene
guitar_root = bpy.data.objects["V206_GUITAR_ROOT"]
original_root = guitar_root.matrix_world.copy()
local_x = Vector((0.819152, 0.0, -0.573576))
local_y = Vector((0.573576, 0.0, 0.819152))
local_z = Vector((0.0, -1.0, 0.0))
location = Vector((-0.570, -0.180, 1.350))
guitar_root.matrix_world = Matrix((
    (local_x.x, local_y.x, local_z.x, location.x),
    (local_x.y, local_y.y, local_z.y, location.y),
    (local_x.z, local_y.z, local_z.z, location.z),
    (0.0, 0.0, 0.0, 1.0),
))
camera = bpy.data.objects.get("V205_CAM_FRONT") or bpy.data.objects.get("V202_CAM_BODY_FRONT")
if camera is None:
    raise RuntimeError("No full-character camera")
scene.camera = camera
for obj in bpy.data.objects:
    if obj.type == "LIGHT":
        obj.hide_render = not obj.name.startswith("V205_")
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = 24
scene.cycles.use_denoising = True
scene.render.resolution_x = 720
scene.render.resolution_y = 960
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.view_settings.look = "AgX - Medium High Contrast"
scene.view_settings.exposure = -1.2
output = root / "production_v207_hands" / "analysis" / "v208_integration_preview.png"
scene.render.filepath = str(output)
bpy.ops.render.render(write_still=True)
guitar_root.matrix_world = original_root
print(f"V208_INTEGRATION_PREVIEW_OK path={output}")
