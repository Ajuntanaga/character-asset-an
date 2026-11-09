from pathlib import Path

import bpy


SOURCE = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An/production_v221_identity_cleanup/Character_An_identity_cleanup_v221.blend")
if not SOURCE.exists():
    raise RuntimeError(f"Missing checkpoint: {SOURCE}")
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
print(f"OPENED_V221={bpy.data.filepath}")
