"""Inspect V276I eye hierarchy and mouth shape-key regions."""

import json
import bpy


head = bpy.data.objects["V276E_GEO-head_animation_realistic"]
keys = head.data.shape_keys.key_blocks
identity = keys["IDENTITY_LANDMARK_WARP"]

eyes = []
for obj in sorted((item for item in bpy.data.objects if "iris" in item.name.lower() or "sclera" in item.name.lower()), key=lambda item: item.name):
    eyes.append({
        "name": obj.name,
        "parent": obj.parent.name if obj.parent else None,
        "location": list(obj.location),
        "rotation_euler": list(obj.rotation_euler),
        "world_translation": list(obj.matrix_world.translation),
        "dimensions": list(obj.dimensions),
        "local_axes_world": [list(obj.matrix_world.to_3x3().col[index].normalized()) for index in range(3)],
        "mesh_local_bounds": {
            "min": [min(vertex.co[axis] for vertex in obj.data.vertices) for axis in range(3)],
            "max": [max(vertex.co[axis] for vertex in obj.data.vertices) for axis in range(3)],
            "centroid": [sum(vertex.co[axis] for vertex in obj.data.vertices) / len(obj.data.vertices) for axis in range(3)],
        } if obj.type == "MESH" and obj.data.vertices else None,
    })

shape_regions = {}
for name in ("CTRL_Smile", "CTRL_JawOpen", "CTRL_Frown", "CTRL_Phoneme_O", "CTRL_Phoneme_E", "CTRL_Phoneme_M", "CTRL_CheekPuff"):
    if name not in keys:
        continue
    key = keys[name]
    moved = []
    for index, (base, point) in enumerate(zip(identity.data, key.data)):
        distance = (point.co - base.co).length
        if distance > 1e-7:
            world = head.matrix_world @ base.co
            moved.append((distance, index, list(world)))
    moved.sort(reverse=True)
    coords = [entry[2] for entry in moved]
    shape_regions[name] = {
        "count": len(moved),
        "bounds": {
            "min": [min(coord[axis] for coord in coords) for axis in range(3)] if coords else None,
            "max": [max(coord[axis] for coord in coords) for axis in range(3)] if coords else None,
        },
        "largest": moved[:16],
    }

print("V276I_FACE_INSPECTION=" + json.dumps({"eyes": eyes, "shape_regions": shape_regions}, sort_keys=True))
