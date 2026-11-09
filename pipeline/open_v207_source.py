from pathlib import Path
import bpy

root = Path(__file__).resolve().parents[1]
source = root / "production_v207_hands" / "ant_playable_hands_v207.blend"
bpy.ops.wm.open_mainfile(filepath=str(source))
print(f"OPEN_V207_OK filepath={bpy.data.filepath}")
