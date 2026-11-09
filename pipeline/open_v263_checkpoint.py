from pathlib import Path
import bpy
path=Path("/home/ajuntanaga/Projects/Blender/Character Asset_An/production_v263_tailoring_details/Character_An_tailoring_details_v263.blend")
bpy.ops.wm.open_mainfile(filepath=str(path));print(f"OPENED_V263={path}")
