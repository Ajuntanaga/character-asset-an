from __future__ import annotations

import sys
from pathlib import Path

import bpy


STAGE_ROOT = Path(__file__).resolve().parents[1]
if str(STAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(STAGE_ROOT))

from pipeline.build_v200_final import build_hair_part_line


for name in (
    "V200_HAIR_PART_LINE",
    "V200_HAIR_PART_COVER",
    "V200_HAIR_PART_EDGE_A",
    "V200_HAIR_PART_EDGE_B",
):
    obj = bpy.data.objects.get(name)
    if obj:
        bpy.data.objects.remove(obj, do_unlink=True)

print("HAIR_RIBBON_OBJECTS=" + ",".join(build_hair_part_line()))
output = STAGE_ROOT / "production_v200_final" / "hair_ribbon_test.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(output), check_existing=False)
scene = bpy.context.scene
scene.camera = bpy.data.objects["V95_CAM_HEAD_FRONT"]
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 600
scene.render.resolution_y = 600
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = str(STAGE_ROOT / "production_v200_final" / "hair_ribbon_test_front.png")
bpy.ops.render.render(write_still=True)
