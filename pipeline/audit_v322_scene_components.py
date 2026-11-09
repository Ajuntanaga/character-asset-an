"""Inventory renderable character, wardrobe, groom, and instrument components."""

from pathlib import Path
import json

import bpy


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
OUTPUT = ROOT / "production_v322_character_rebuild" / "audit" / "v322_scene_components.json"


def bounds(obj):
    if not obj.bound_box:
        return None
    points = [obj.matrix_world @ __import__("mathutils").Vector(corner) for corner in obj.bound_box]
    lower = [min(point[axis] for point in points) for axis in range(3)]
    upper = [max(point[axis] for point in points) for axis in range(3)]
    return {"min": lower, "max": upper, "size": [upper[i] - lower[i] for i in range(3)]}


def main():
    objects = []
    for obj in sorted(bpy.data.objects, key=lambda item: item.name.lower()):
        if obj.type not in {"MESH", "CURVES", "CURVE", "ARMATURE"}:
            continue
        entry = {
            "name": obj.name,
            "type": obj.type,
            "hide_render": obj.hide_render,
            "hide_viewport": obj.hide_viewport,
            "parent": obj.parent.name if obj.parent else None,
            "parent_type": obj.parent_type,
            "parent_bone": obj.parent_bone,
            "collections": [collection.name for collection in obj.users_collection],
            "bounds": bounds(obj),
            "materials": [slot.material.name if slot.material else None for slot in obj.material_slots],
            "modifiers": [
                {
                    "name": modifier.name,
                    "type": modifier.type,
                    "object": getattr(getattr(modifier, "object", None), "name", None),
                }
                for modifier in obj.modifiers
            ],
        }
        if obj.type == "MESH":
            entry.update({
                "vertices": len(obj.data.vertices),
                "polygons": len(obj.data.polygons),
                "shape_keys": len(obj.data.shape_keys.key_blocks) - 1 if obj.data.shape_keys else 0,
                "vertex_groups": len(obj.vertex_groups),
            })
        elif obj.type == "ARMATURE":
            entry["bones"] = len(obj.data.bones)
        objects.append(entry)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "blend": bpy.data.filepath,
        "scene": bpy.context.scene.name,
        "objects": objects,
    }
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print("V322_SCENE_COMPONENT_AUDIT=" + json.dumps({
        "output": str(OUTPUT),
        "objects": len(objects),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
