from pathlib import Path
import bpy

path = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An/production_v270_boot_finish_cuffs/Character_An_boot_finish_cuffs_v270.blend")
bpy.ops.wm.open_mainfile(filepath=str(path), load_ui=False)
print(f"OPENED_V270={path}")
