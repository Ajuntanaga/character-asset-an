"""Open the accepted V241 wardrobe foundation in a separate MCP call."""

from pathlib import Path

import bpy


SOURCE = Path(
    "/home/ajuntanaga/Projects/Blender/Character Asset_An/"
    "production_v241_rigged_wardrobe_foundation/"
    "Character_An_rigged_wardrobe_v241.blend"
)

bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
print(f"OPENED_V241={bpy.data.filepath}")
