from pathlib import Path
import bpy

path=Path("/home/ajuntanaga/Projects/Blender/Character Asset_An/production_v262_long_sleeve_jacket/Character_An_long_sleeve_jacket_v262.blend")
bpy.ops.wm.open_mainfile(filepath=str(path))
print(f"OPENED_V262={path}")
