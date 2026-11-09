"""Inventory reusable identity assets already carried inside V310."""

from pathlib import Path
import json

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v310_reom_scene_alignment" / "Character_An_reom_scene_alignment_v310.blend"


def bounds(obj):
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    return {
        "min": [min(point[axis] for point in points) for axis in range(3)],
        "max": [max(point[axis] for point in points) for axis in range(3)],
    }


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    records = {}
    tokens = ("V216_", "V217_", "V274D_", "V279_", "HAIR", "GROOM", "BEARD", "MUSTACHE", "BROW")
    for obj in bpy.data.objects:
        if any(token in obj.name.upper() for token in tokens):
            shape_keys = []
            if obj.type == "MESH" and obj.data.shape_keys:
                shape_keys = [key.name for key in obj.data.shape_keys.key_blocks]
            records[obj.name] = {
                "type": obj.type,
                "hide_render": obj.hide_render,
                "hide_viewport": obj.hide_viewport,
                "parent": obj.parent.name if obj.parent else None,
                "parent_type": obj.parent_type,
                "parent_bone": obj.parent_bone,
                "bounds": bounds(obj) if obj.type in {"MESH", "CURVE"} else None,
                "shape_key_count": max(0, len(shape_keys) - 1),
                "shape_key_names": shape_keys[1:],
            }
    body = bpy.data.objects["V310_REOM_BODY"]
    records[body.name] = {
        "type": body.type,
        "hide_render": body.hide_render,
        "bounds": bounds(body),
        "vertices": len(body.data.vertices),
        "modifiers": [{"name": modifier.name, "type": modifier.type} for modifier in body.modifiers],
    }
    print("V310_IDENTITY_STACK=" + json.dumps(records, sort_keys=True))


if __name__ == "__main__":
    main()
