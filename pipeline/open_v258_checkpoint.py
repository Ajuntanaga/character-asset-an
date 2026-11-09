from pathlib import Path
import bpy

path = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An/production_v258_collision_aware_fretting/Character_An_collision_aware_fretting_v258.blend")
bpy.ops.wm.open_mainfile(filepath=str(path))
print(f"OPENED_V258={path}")
