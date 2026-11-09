from pathlib import Path
import bpy

path = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An/production_v249_hand_bind_repair/Character_An_hand_bind_v249.blend")
bpy.ops.wm.open_mainfile(filepath=str(path))
print(f"OPENED_V249_BIND={path}")
