from pathlib import Path
import bpy

path = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An/production_v276h_facial_deformation_proof/Character_An_facial_deformation_v276h.blend")
if not path.exists():
    raise RuntimeError(f"Missing checkpoint: {path}")
bpy.ops.wm.open_mainfile(filepath=str(path), load_ui=False)
print(f"OPENED_V276H={bpy.data.filepath}")
