import json

import bpy
from mathutils import Vector


body = bpy.data.objects["V211_BODY_NEUTRAL"]
world_points = [body.matrix_world @ vertex.co for vertex in body.data.vertices]
payload = {
    "filepath": bpy.data.filepath,
    "body": body.name,
    "vertices": len(body.data.vertices),
    "polygons": len(body.data.polygons),
    "bounds": {
        axis: [round(min(point[index] for point in world_points), 6), round(max(point[index] for point in world_points), 6)]
        for index, axis in enumerate(("x", "y", "z"))
    },
    "modifiers": [
        {
            "name": modifier.name,
            "type": modifier.type,
            "object": modifier.object.name if modifier.type == "ARMATURE" and modifier.object else None,
        }
        for modifier in body.modifiers
    ],
    "materials": sorted(material.name for material in bpy.data.materials),
    "groups": sorted(group.name for group in body.vertex_groups),
}
print("V240_WARDROBE_INSPECT=" + json.dumps(payload, sort_keys=True))
