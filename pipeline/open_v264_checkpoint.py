from pathlib import Path
import bpy
path=Path("/home/ajuntanaga/Projects/Blender/Character Asset_An/production_v264_waist_cleanup/Character_An_waist_cleanup_v264.blend")
bpy.ops.wm.open_mainfile(filepath=str(path));print(f"OPENED_V264={path}")
