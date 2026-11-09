import json
import bpy

head = bpy.data.objects["V216_REFERENCE_FITTED_HEAD"]
points = [head.matrix_world @ vertex.co for vertex in head.data.vertices]
print("V271_HEAD_BOUNDS=" + json.dumps({
    "vertices": len(points),
    "polygons": len(head.data.polygons),
    "bounds": {
        "x": [min(p.x for p in points), max(p.x for p in points)],
        "y": [min(p.y for p in points), max(p.y for p in points)],
        "z": [min(p.z for p in points), max(p.z for p in points)],
    },
    "materials": [slot.material.name if slot.material else None for slot in head.material_slots],
    "modifiers": [mod.type for mod in head.modifiers],
}, sort_keys=True))
