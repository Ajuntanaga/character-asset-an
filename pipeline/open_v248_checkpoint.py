from pathlib import Path
import bpy

path = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An/production_v248_topology_hand_replacement/Character_An_topology_hand_v248.blend")
bpy.ops.wm.open_mainfile(filepath=str(path))
print(f"OPENED_V248={path}")
