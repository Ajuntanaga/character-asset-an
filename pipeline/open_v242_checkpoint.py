"""Open the V242 tailored wardrobe checkpoint in a separate MCP call."""

from pathlib import Path

import bpy


SOURCE = Path(
    "/home/ajuntanaga/Projects/Blender/Character Asset_An/"
    "production_v242_tailoring_collar/Character_An_tailored_wardrobe_v242.blend"
)

bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
print(f"OPENED_V242={bpy.data.filepath}")
