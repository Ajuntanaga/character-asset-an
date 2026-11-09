import json
import bpy
from mathutils import Vector

head = bpy.data.objects["V216_REFERENCE_FITTED_HEAD"]
record = {}
for side, center in (("L", Vector((0.035, -0.100, 1.681))), ("R", Vector((-0.035, -0.100, 1.681)))):
    points = [(head.matrix_world @ vertex.co, vertex.index) for vertex in head.data.vertices]
    points.sort(key=lambda item: (item[0] - center).length)
    nearest = points[:120]
    record[side] = {
        "closest": [[idx, round(p.x, 5), round(p.y, 5), round(p.z, 5), round((p-center).length, 5)] for p, idx in nearest[:20]],
        "bounds120": {
            "x": [min(p.x for p, _ in nearest), max(p.x for p, _ in nearest)],
            "y": [min(p.y for p, _ in nearest), max(p.y for p, _ in nearest)],
            "z": [min(p.z for p, _ in nearest), max(p.z for p, _ in nearest)],
        },
    }
print("V276_EYE_SURFACE=" + json.dumps(record, sort_keys=True))
