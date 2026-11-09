"""Print compact eye hierarchy geometry data."""

import json
import bpy


result = []
for obj in sorted((item for item in bpy.data.objects if "iris" in item.name.lower() or "sclera" in item.name.lower()), key=lambda item: item.name):
    vertices = list(obj.data.vertices) if obj.type == "MESH" else []
    result.append({
        "name": obj.name,
        "parent": obj.parent.name if obj.parent else None,
        "world_translation": list(obj.matrix_world.translation),
        "local_bounds": {
            "min": [min(vertex.co[axis] for vertex in vertices) for axis in range(3)],
            "max": [max(vertex.co[axis] for vertex in vertices) for axis in range(3)],
            "centroid": [sum(vertex.co[axis] for vertex in vertices) / len(vertices) for axis in range(3)],
        } if vertices else None,
    })

print("V276I_EYE_INSPECTION=" + json.dumps(result, sort_keys=True))
