from pathlib import Path
import bpy

path = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An/production_v250_dedicated_hand_rig/Character_An_dedicated_hand_rig_v250.blend")
bpy.ops.wm.open_mainfile(filepath=str(path))
print(f"OPENED_V250={path}")
