from pathlib import Path
import bpy

root = Path(__file__).resolve().parents[1]
source = root / "production_v208_rig" / "ant_performance_rig_v208.blend"
bpy.ops.wm.open_mainfile(filepath=str(source))
print(f"OPEN_V208_OK filepath={bpy.data.filepath}")
