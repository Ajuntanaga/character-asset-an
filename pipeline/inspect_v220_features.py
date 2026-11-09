import bpy

for obj in bpy.data.objects:
    name = obj.name.lower()
    if any(key in name for key in ("eye", "iris", "pupil", "brow", "beard", "stubble", "hair")):
        print({
            "name": obj.name,
            "type": obj.type,
            "location": [round(value, 4) for value in obj.location],
            "dimensions": [round(value, 4) for value in obj.dimensions],
            "parent": obj.parent.name if obj.parent else None,
        })
