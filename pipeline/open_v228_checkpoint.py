from pathlib import Path

import bpy

path = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An/production_v228_garment_rig_coupling/Character_An_garment_rig_v228.blend")
bpy.ops.wm.open_mainfile(filepath=str(path))
print({"status": "ok", "filepath": bpy.data.filepath})
