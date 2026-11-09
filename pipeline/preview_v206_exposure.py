from __future__ import annotations

import sys
from pathlib import Path

import bpy
from mathutils import Matrix


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


root = bpy.data.objects["V206_GUITAR_ROOT"]
prior_matrix = root.matrix_world.copy()
prior_visibility = {obj.name: obj.hide_render for obj in bpy.data.objects}
root.matrix_world = Matrix.Identity(4)
for obj in bpy.data.objects:
    if not obj.name.startswith("V206_"):
        obj.hide_render = True
scene = bpy.context.scene
scene.view_settings.exposure = -2.0
scene.camera = bpy.data.objects["V206_CAM_BEAUTY"]
scene.render.resolution_x = 900
scene.render.resolution_y = 640
scene.render.resolution_percentage = 100
scene.render.filepath = str(ROOT / "production_v206_guitar" / "analysis" / "exposure_preview.png")
Path(scene.render.filepath).parent.mkdir(parents=True, exist_ok=True)
bpy.ops.render.render(write_still=True)
root.matrix_world = prior_matrix
for name, hidden in prior_visibility.items():
    obj = bpy.data.objects.get(name)
    if obj is not None:
        obj.hide_render = hidden
print("V206_EXPOSURE_PREVIEW_OK")
