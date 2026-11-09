"""Open the V243 wardrobe/footwear checkpoint in a separate MCP call."""

from pathlib import Path

import bpy


SOURCE = Path(
    "/home/ajuntanaga/Projects/Blender/Character Asset_An/"
    "production_v243_trousers_boots/Character_An_trousers_boots_v243.blend"
)

bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
print(f"OPENED_V243={bpy.data.filepath}")
