from pathlib import Path
import bpy

path = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An/production_v276e_head_hierarchy_jaw/Character_An_head_hierarchy_jaw_v276e.blend")
if not path.exists():
    raise RuntimeError(f"Missing checkpoint: {path}")
bpy.ops.wm.open_mainfile(filepath=str(path), load_ui=False)
print(f"OPENED_V276E={bpy.data.filepath}")
