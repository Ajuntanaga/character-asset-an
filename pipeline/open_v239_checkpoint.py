from pathlib import Path

import bpy


SOURCE = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An/production_v239_clean_auto_rig/Character_An_clean_auto_rig_v239.blend")
if not SOURCE.exists():
    raise RuntimeError(f"Missing checkpoint: {SOURCE}")
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
print(f"OPENED_V239={bpy.data.filepath}")
