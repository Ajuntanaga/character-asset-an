from pathlib import Path
import bpy


path = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An/production_v276j_corrected_facial_controls/Character_An_corrected_facial_controls_v276j.blend")
if not path.exists():
    raise RuntimeError(f"Missing checkpoint: {path}")
bpy.ops.wm.open_mainfile(filepath=str(path), load_ui=False)
print(f"OPENED_V276J={bpy.data.filepath}")
