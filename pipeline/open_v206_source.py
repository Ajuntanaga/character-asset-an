from pathlib import Path
import bpy

root = Path(__file__).resolve().parents[1]
source = root / "production_v206_guitar" / "ant_headless_guitar_v206.blend"
bpy.ops.wm.open_mainfile(filepath=str(source))
print(f"OPEN_V206_OK filepath={bpy.data.filepath}")
