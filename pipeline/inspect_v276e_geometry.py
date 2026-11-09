import json
import bpy
from mathutils import Vector

records = {}
for obj in bpy.data.objects:
    if obj.name.startswith("V276E_") and obj.type == "MESH":
        points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
        low = [min(point[index] for point in points) for index in range(3)]
        high = [max(point[index] for point in points) for index in range(3)]
        records[obj.name] = {
            "low": low,
            "high": high,
            "center": [(low[index] + high[index]) * 0.5 for index in range(3)],
            "dimensions": [high[index] - low[index] for index in range(3)],
        }
print("V276E_GEOMETRY=" + json.dumps(records, sort_keys=True))

profiles = {}
for name in ("V216_REFERENCE_FITTED_HEAD", "V276E_GEO-head_animation_realistic"):
    obj = bpy.data.objects.get(name)
    if not obj or obj.type != "MESH":
        continue
    bands = {}
    for low in (1.48, 1.50, 1.52, 1.54, 1.56, 1.58, 1.60):
        points = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
        selected = [point for point in points if low <= point.z < low + 0.02 and abs(point.x) < 0.06]
        if selected:
            bands[f"{low:.2f}-{low + 0.02:.2f}"] = {
                "front_y": min(point.y for point in selected),
                "back_y": max(point.y for point in selected),
                "count": len(selected),
            }
    profiles[name] = bands
print("V276E_FACE_PROFILE=" + json.dumps(profiles, sort_keys=True))
