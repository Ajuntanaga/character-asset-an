from pathlib import Path
import bpy
path=Path("/home/ajuntanaga/Projects/Blender/Character Asset_An/production_v265_neutral_wardrobe_inspection/Character_An_neutral_wardrobe_inspection_v265.blend")
bpy.ops.wm.open_mainfile(filepath=str(path));print(f"OPENED_V265={path}")
