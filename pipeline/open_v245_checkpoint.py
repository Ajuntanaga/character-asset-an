"""Open the V245 arm-pose checkpoint in a separate MCP call."""

from pathlib import Path

import bpy


SOURCE = Path(
    "/home/ajuntanaga/Projects/Blender/Character Asset_An/"
    "production_v245_arm_performance_pose/Character_An_arm_performance_v245.blend"
)

bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
print(f"OPENED_V245={bpy.data.filepath}")
