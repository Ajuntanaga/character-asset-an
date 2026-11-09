from pathlib import Path

import bpy


SOURCE = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An/production_v240_identity_clean_rig/Character_An_identity_clean_rig_v240.blend")
if not SOURCE.exists():
    raise RuntimeError(f"Missing checkpoint: {SOURCE}")
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
print(f"OPENED_V240={bpy.data.filepath}")
