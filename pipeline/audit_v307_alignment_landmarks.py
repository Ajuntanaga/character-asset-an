"""Report only the Reom landmarks needed to align it with the V300 scene."""

from pathlib import Path
import json

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v307_charmorph_reom_rig" / "Character_An_reom_rig_v307.blend"


def world_bbox(obj):
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    return {
        "min": [min(point[axis] for point in points) for axis in range(3)],
        "max": [max(point[axis] for point in points) for axis in range(3)],
    }


def bone_record(rig, name):
    bone = rig.pose.bones.get(name)
    if bone is None:
        return None
    return {
        "head_world": list(rig.matrix_world @ bone.head),
        "tail_world": list(rig.matrix_world @ bone.tail),
        "parent": bone.parent.name if bone.parent else None,
    }


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    body = bpy.data.objects["V307_REOM_BODY"]
    rig = bpy.data.objects["V307_REOM_RIG"]
    wanted = [
        "root",
        "torso",
        "hips",
        "chest",
        "chest_fk",
        "neck",
        "head",
        "shoulder.L",
        "shoulder.R",
        "upper_arm_fk.L",
        "upper_arm_fk.R",
        "forearm_fk.L",
        "forearm_fk.R",
        "hand_fk.L",
        "hand_fk.R",
        "hand_ik.L",
        "hand_ik.R",
        "DEF-pelvis.L",
        "DEF-pelvis.R",
        "DEF-spine",
        "DEF-spine.001",
        "DEF-spine.002",
        "DEF-spine.003",
        "DEF-spine.004",
        "DEF-spine.005",
        "DEF-spine.006",
        "DEF-upper_arm.L",
        "DEF-upper_arm.R",
        "DEF-forearm.L",
        "DEF-forearm.R",
        "DEF-hand.L",
        "DEF-hand.R",
        "DEF-thigh.L",
        "DEF-thigh.R",
        "DEF-shin.L",
        "DEF-shin.R",
        "DEF-foot.L",
        "DEF-foot.R",
        "DEF-head",
    ]
    arm_names = sorted(
        name
        for name in rig.pose.bones.keys()
        if (
            name.startswith(("upper_arm_", "forearm_", "hand_", "thigh_", "foot_"))
            or name in {"root", "torso", "hips", "chest", "chest_fk", "neck", "head"}
        )
    )
    record = {
        "source": str(SOURCE.relative_to(ROOT)),
        "body": {
            "matrix_world": [list(row) for row in body.matrix_world],
            "dimensions": list(body.dimensions),
            "bbox_world": world_bbox(body),
            "parent": body.parent.name if body.parent else None,
            "armature_modifier": next(
                (modifier.object.name for modifier in body.modifiers if modifier.type == "ARMATURE" and modifier.object),
                None,
            ),
        },
        "rig": {
            "matrix_world": [list(row) for row in rig.matrix_world],
            "display_type": rig.display_type,
            "landmarks": {name: item for name in wanted if (item := bone_record(rig, name)) is not None},
            "relevant_control_names": arm_names,
        },
        "collections": {
            collection.name: {
                "count": len(collection.objects),
                "members": sorted(obj.name for obj in collection.objects)[:30],
                "contains_body": collection.objects.get(body.name) is not None,
                "contains_rig": collection.objects.get(rig.name) is not None,
            }
            for collection in bpy.data.collections
        },
    }
    print("V307_ALIGNMENT_LANDMARKS=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
