from pathlib import Path

import bpy
from mathutils import Vector

path = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An/production_v232_v198_hybrid_world_head/Character_An_v198_hybrid_v232.blend")
bpy.ops.wm.open_mainfile(filepath=str(path))
root = bpy.data.objects["ANTV1_GUITAR_ROOT"]
print({"root_matrix": [[round(value, 6) for value in row] for row in root.matrix_world]})
for name in ("ANTV1_GUITAR_BODY_EDGE", "ANTV1_GUITAR_NECK", "ANTV1_PICKUP_BRIDGE", "ANTV1_PICKUP_NECK"):
    obj = bpy.data.objects[name]
    corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    center = sum(corners, Vector()) / len(corners)
    print({"name": name, "center": [round(v, 6) for v in center], "dimensions": [round(v, 6) for v in obj.dimensions]})
