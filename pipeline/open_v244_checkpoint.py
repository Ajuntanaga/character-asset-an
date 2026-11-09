"""Open the V244 guitar integration checkpoint in a separate MCP call."""

from pathlib import Path

import bpy


SOURCE = Path(
    "/home/ajuntanaga/Projects/Blender/Character Asset_An/"
    "production_v244_guitar_integration/Character_An_guitar_integration_v244.blend"
)

bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
print(f"OPENED_V244={bpy.data.filepath}")
