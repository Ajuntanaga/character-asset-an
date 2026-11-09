from __future__ import annotations

import bpy


NAMES = (
    "V195_BODY",
    "V195_SHIRT",
    "V195_JACKET",
    "V195_JACKET_COLLAR",
    "V195_SHIRT_COLLAR",
    "V195_SHIRT_COLLAR_STAND",
    "V195_BOOT_L",
    "V195_BOOT_R",
    "V195_BOOT_ELASTIC_L",
    "V195_BOOT_ELASTIC_R",
    "V195_CUFF_L",
    "V195_CUFF_R",
    "V194_HEAD",
    "V194_BEARD",
    "V194_HAIR",
)


def bounds(obj: bpy.types.Object) -> list[list[float]]:
    corners = [obj.matrix_world @ __import__("mathutils").Vector(corner) for corner in obj.bound_box]
    return [
        [round(min(point[index] for point in corners), 5) for index in range(3)],
        [round(max(point[index] for point in corners), 5) for index in range(3)],
    ]


for name in NAMES:
    obj = bpy.data.objects.get(name)
    if obj is None:
        print(f"FINAL_PREP {name} MISSING")
        continue
    print(
        "FINAL_PREP",
        name,
        "type=", obj.type,
        "hide_render=", obj.hide_render,
        "location=", tuple(round(float(value), 5) for value in obj.location),
        "dimensions=", tuple(round(float(value), 5) for value in obj.dimensions),
        "bounds=", bounds(obj),
        "modifiers=", [(modifier.name, modifier.type) for modifier in obj.modifiers],
    )

scene = bpy.context.scene
armature = bpy.data.objects.get("V197_RIG")
print("FINAL_PREP scene action", armature.animation_data.action.name if armature and armature.animation_data and armature.animation_data.action else None)
print("FINAL_PREP frame", scene.frame_current)
print("FINAL_PREP cameras", sorted(obj.name for obj in bpy.data.objects if obj.type == "CAMERA" and (obj.name.startswith("V151_") or obj.name.startswith("V95_") or obj.name.startswith("V142_") or obj.name.startswith("V166_"))))

for obj in sorted(bpy.data.objects, key=lambda item: item.name):
    if obj.hide_render or obj.type in {"CAMERA", "LIGHT", "ARMATURE"}:
        continue
    materials = [slot.material.name if slot.material else None for slot in obj.material_slots]
    collections = [collection.name for collection in obj.users_collection]
    print("FINAL_VISIBLE", obj.name, "type=", obj.type, "materials=", materials, "collections=", collections)
