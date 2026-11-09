"""Open the V246 exact-contact pose checkpoint in a separate MCP call."""

from pathlib import Path

import bpy


SOURCE = Path(
    "/home/ajuntanaga/Projects/Blender/Character Asset_An/"
    "production_v246_exact_fretting_solve/Character_An_exact_fretting_v246.blend"
)

bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
print(f"OPENED_V246={bpy.data.filepath}")
