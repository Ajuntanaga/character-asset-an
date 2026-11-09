from pathlib import Path
import bpy


path = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An/production_v274a_identity_lookdev/Character_An_identity_lookdev_v274a.blend")
if not path.exists():
    raise RuntimeError(f"Missing checkpoint: {path}")
bpy.ops.wm.open_mainfile(filepath=str(path), load_ui=False)
print(f"OPENED_V274A={bpy.data.filepath}")
