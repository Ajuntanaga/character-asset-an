from pathlib import Path
import bpy


path = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An/production_v277b_ik_target_matrix/Character_An_ik_target_matrix_v277b.blend")
if not path.exists():
    raise RuntimeError(f"Missing checkpoint: {path}")
bpy.ops.wm.open_mainfile(filepath=str(path), load_ui=False)
print(f"OPENED_V277B={bpy.data.filepath}")
