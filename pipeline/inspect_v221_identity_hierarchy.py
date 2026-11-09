import json

import bpy


names = [
    "V216_REFERENCE_FITTED_HEAD",
    "V216_EYE_L", "V216_EYE_R",
    "V216_IRIS_L", "V216_IRIS_R",
    "V216_PUPIL_L", "V216_PUPIL_R",
    "V217_TIGHT_CURL_GROOM", "V217_CURL_CLUSTERS",
    "V217_BROWS", "V217_BEARD_STUBBLE",
]
payload = {}
for name in names:
    obj = bpy.data.objects.get(name)
    if obj is None:
        continue
    payload[name] = {
        "type": obj.type,
        "parent": obj.parent.name if obj.parent else None,
        "parent_type": obj.parent_type,
        "parent_bone": obj.parent_bone,
        "matrix_world": [[round(value, 9) for value in row] for row in obj.matrix_world],
        "matrix_local": [[round(value, 9) for value in row] for row in obj.matrix_local],
        "dimensions": [round(value, 9) for value in obj.dimensions],
    }
print("V221_HIERARCHY=" + json.dumps(payload, sort_keys=True))
