import bpy
from mathutils import Vector

for obj in bpy.data.objects:
    if obj.name.startswith("ANTV1_") or obj.name.startswith("V206_"):
        if any(key in obj.name for key in ("BODY", "NECK", "FRETBOARD", "BRIDGE", "PICKUP")):
            corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
            center = sum(corners, Vector()) / len(corners)
            print({
                "name": obj.name,
                "parent": obj.parent.name if obj.parent else None,
                "world": [round(v, 5) for v in obj.matrix_world.translation],
                "local": [round(v, 5) for v in obj.location],
                "dimensions": [round(v, 5) for v in obj.dimensions],
                "bounds_center": [round(v, 5) for v in center],
            })
