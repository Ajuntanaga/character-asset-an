from pathlib import Path

import bpy


SOURCE = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An/production_v237_exact_contact_hand/Character_An_exact_contact_hand_v237.blend")
if not SOURCE.exists():
    raise RuntimeError(f"Missing checkpoint: {SOURCE}")
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
print(f"OPENED_V237={bpy.data.filepath}")
