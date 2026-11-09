from pathlib import Path
import json

import bpy
from mathutils import Vector

ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v300_guitar_visual_acceptance" / "Character_An_guitar_visual_acceptance_v300.blend"
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
records = {}
for obj in bpy.data.objects:
    if obj.type == "ARMATURE" or (obj.type == "MESH" and ("BODY" in obj.name or "CLEAN" in obj.name or "V239" in obj.name)):
        world = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
        records[obj.name] = {
            "type": obj.type,
            "parent": obj.parent.name if obj.parent else None,
            "dimensions": list(obj.dimensions),
            "bbox_min": [min(p[i] for p in world) for i in range(3)],
            "bbox_max": [max(p[i] for p in world) for i in range(3)],
            "vertices": len(obj.data.vertices) if obj.type == "MESH" else None,
            "bones": len(obj.data.bones) if obj.type == "ARMATURE" else None,
        }
        if obj.type == "ARMATURE":
            names = [name for name in obj.pose.bones.keys() if any(token in name.lower() for token in ("hand.l", "hand.r", "head", "root", "spine"))]
            records[obj.name]["landmark_bones"] = {
                name: {
                    "head_world": list(obj.matrix_world @ obj.pose.bones[name].head),
                    "tail_world": list(obj.matrix_world @ obj.pose.bones[name].tail),
                }
                for name in names[:80]
            }
print("V300_REOM_ALIGNMENT=" + json.dumps(records, sort_keys=True))
