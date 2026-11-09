"""Inspect the live V246 hand deformation and material state through Blender MCP."""

import json

import bpy
from mathutils import Vector


def bounds(obj):
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    return {
        "min": [round(min(p[i] for p in points), 6) for i in range(3)],
        "max": [round(max(p[i] for p in points), 6) for i in range(3)],
    }


body = bpy.data.objects.get("V211_BODY_NEUTRAL")
rig = bpy.data.objects.get("V239_CLEAN_CHARACTER_RIG")
record = {
    "filepath": bpy.data.filepath,
    "body": None,
    "rig": None,
    "hand_objects": [],
}
if body:
    record["body"] = {
        "vertices": len(body.data.vertices),
        "polygons": len(body.data.polygons),
        "materials": [slot.material.name if slot.material else None for slot in body.material_slots],
        "material_counts": {
            str(index): sum(1 for polygon in body.data.polygons if polygon.material_index == index)
            for index in range(len(body.material_slots))
        },
        "modifiers": [(mod.name, mod.type, getattr(mod, "object", None).name if getattr(mod, "object", None) else None) for mod in body.modifiers],
        "vertex_groups": len(body.vertex_groups),
        "bounds": bounds(body),
    }
if rig:
    record["rig"] = {
        "pose_position": rig.data.pose_position,
        "scale": [round(v, 6) for v in rig.scale],
        "def_hands": {
            side: {
                "head": [round(float(v), 6) for v in (rig.matrix_world @ rig.pose.bones[f"DEF-hand.{side}"].head)],
                "tail": [round(float(v), 6) for v in (rig.matrix_world @ rig.pose.bones[f"DEF-hand.{side}"].tail)],
            }
            for side in ("L", "R")
        },
    }
    record["rig"]["left_digit_chain"] = {
        name: {
            "head": [round(float(v), 6) for v in (rig.matrix_world @ bone.head)],
            "tail": [round(float(v), 6) for v in (rig.matrix_world @ bone.tail)],
            "rotation": [round(float(v), 6) for v in bone.rotation_euler],
        }
        for name, bone in rig.pose.bones.items()
        if name.startswith(("DEF-f_index", "DEF-f_middle", "DEF-f_ring", "DEF-f_pinky", "DEF-thumb")) and name.endswith(".L")
    }
    record["rig"]["left_rest_chain"] = {
        name: {
            "head": [round(float(v), 6) for v in (rig.matrix_world @ bone.head_local)],
            "tail": [round(float(v), 6) for v in (rig.matrix_world @ bone.tail_local)],
        }
        for name, bone in rig.data.bones.items()
        if name in {"DEF-hand.L", "DEF-forearm.L"}
        or (name.startswith(("DEF-f_index", "DEF-f_middle", "DEF-f_ring", "DEF-f_pinky", "DEF-thumb")) and name.endswith(".L"))
    }
for obj in bpy.context.scene.objects:
    name = obj.name.lower()
    if any(token in name for token in ("hand", "finger", "thumb", "nail")) and obj.type == "MESH":
        record["hand_objects"].append({
            "name": obj.name,
            "visible": not obj.hide_render,
            "materials": [slot.material.name if slot.material else None for slot in obj.material_slots],
            "bounds": bounds(obj),
        })
print("V246_FAILURE_INSPECT=" + json.dumps(record, sort_keys=True))
