"""Report visible mesh objects intersecting the fretting-hand performance region."""

import json

import bpy
from mathutils import Vector


depsgraph = bpy.context.evaluated_depsgraph_get()
items = []
for obj in bpy.context.scene.objects:
    if obj.type != "MESH" or obj.hide_render:
        continue
    evaluated = obj.evaluated_get(depsgraph)
    points = [evaluated.matrix_world @ Vector(corner) for corner in evaluated.bound_box]
    minimum = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
    maximum = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
    if maximum.x < 0.10 or minimum.x > 0.50 or maximum.y < -0.65 or minimum.y > -0.15 or maximum.z < 1.15 or minimum.z > 1.65:
        continue
    items.append({
        "name": obj.name,
        "bounds": {"min": [round(v, 4) for v in minimum], "max": [round(v, 4) for v in maximum]},
        "materials": [slot.material.name if slot.material else None for slot in obj.material_slots],
        "modifiers": [(modifier.name, modifier.type) for modifier in obj.modifiers],
    })
print("HAND_OVERLAP=" + json.dumps(items, sort_keys=True))
