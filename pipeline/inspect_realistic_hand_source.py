"""Append and inspect the bundled standalone realistic hand source."""

import json
from pathlib import Path

import bpy
from mathutils import Vector


path = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An/third_party/blender_human_base_meshes/v1.4.1/human-base-meshes-bundle-v1.4.1/human_base_meshes_bundle.blend")
names = ["realistic_hand", "Hand  - Realistic"]
with bpy.data.libraries.load(str(path), link=False) as (source, target):
    target.objects = names
record = []
for obj in target.objects:
    if obj.name not in bpy.context.scene.objects:
        bpy.context.scene.collection.objects.link(obj)
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    item = {
        "name": obj.name,
        "type": obj.type,
        "data": obj.data.name if obj.data else None,
        "dimensions": [round(float(v), 6) for v in obj.dimensions],
        "bounds": {
            "min": [round(min(p[i] for p in points), 6) for i in range(3)],
            "max": [round(max(p[i] for p in points), 6) for i in range(3)],
        },
    }
    if obj.type == "MESH":
        item.update({
            "vertices": len(obj.data.vertices),
            "polygons": len(obj.data.polygons),
            "modifiers": [(modifier.name, modifier.type) for modifier in obj.modifiers],
            "materials": [slot.material.name if slot.material else None for slot in obj.material_slots],
        })
    record.append(item)
print("REALISTIC_HAND_SOURCE=" + json.dumps(record, sort_keys=True))
for obj in target.objects:
    bpy.data.objects.remove(obj, do_unlink=True)
