from pathlib import Path

import bpy


SOURCE = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An/production_v211_clean_base/Character_An_clean_base_v211.blend")
if not SOURCE.exists():
    raise RuntimeError(f"Missing checkpoint: {SOURCE}")
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
print(f"OPENED_V211={bpy.data.filepath}")
