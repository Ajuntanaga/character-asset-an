from pathlib import Path
import bpy

path = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An/production_v247_anatomical_fretting/Character_An_anatomical_fretting_v247.blend")
bpy.ops.wm.open_mainfile(filepath=str(path))
print(f"OPENED_V247={path}")
