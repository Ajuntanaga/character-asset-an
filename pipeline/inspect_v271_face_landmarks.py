import json
import bpy

record = {}
for name in ("V216_EYE_L", "V216_EYE_R", "V221_BROW_L", "V221_BROW_R"):
    obj = bpy.data.objects.get(name)
    if obj:
        record[name] = {
            "location": [round(v, 6) for v in obj.matrix_world.translation],
            "dimensions": [round(v, 6) for v in obj.dimensions],
        }
print("V271_FACE_LANDMARKS=" + json.dumps(record, sort_keys=True))
