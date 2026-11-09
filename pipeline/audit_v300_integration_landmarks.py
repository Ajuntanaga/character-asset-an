"""Report only the scene landmarks needed to integrate the Reom rig into V300."""

from pathlib import Path
import json

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v300_guitar_visual_acceptance" / "Character_An_guitar_visual_acceptance_v300.blend"


def vec(value):
    return [float(component) for component in value]


def world_bbox(obj):
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    return {
        "min": [min(point[axis] for point in points) for axis in range(3)],
        "max": [max(point[axis] for point in points) for axis in range(3)],
    }


def object_record(obj):
    return {
        "type": obj.type,
        "parent": obj.parent.name if obj.parent else None,
        "matrix_world": [list(row) for row in obj.matrix_world],
        "bbox_world": world_bbox(obj) if obj.type in {"MESH", "CURVE", "SURFACE", "FONT"} else None,
        "dimensions": vec(obj.dimensions),
        "visible_render": not obj.hide_render,
    }


def bone_record(rig, name):
    bone = rig.pose.bones.get(name)
    if bone is None:
        return None
    return {
        "head_world": vec(rig.matrix_world @ bone.head),
        "tail_world": vec(rig.matrix_world @ bone.tail),
        "matrix_world": [list(row) for row in rig.matrix_world @ bone.matrix],
        "parent": bone.parent.name if bone.parent else None,
    }


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    object_names = [
        "V211_BODY_NEUTRAL",
        "V239_CLEAN_CHARACTER_RIG",
        "V239_METARIG",
        "V206_GUITAR_ROOT",
        "V250_FRETTING_HAND_RIG",
        "V292_PICKING_HAND_RIG",
    ]
    bones = [
        "root",
        "torso",
        "hips",
        "chest",
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
        "DEF-foot.L",
        "DEF-foot.R",
    ]
    rigs = {}
    for rig_name in ("V239_CLEAN_CHARACTER_RIG", "V239_METARIG"):
        rig = bpy.data.objects.get(rig_name)
        if rig is None:
            continue
        rigs[rig_name] = {
            "matrix_world": [list(row) for row in rig.matrix_world],
            "landmarks": {name: item for name in bones if (item := bone_record(rig, name)) is not None},
        }

    guitar_objects = {}
    for obj in bpy.data.objects:
        upper = obj.name.upper()
        if any(token in upper for token in ("GUITAR", "FRET", "STRING", "NECK", "BRIDGE", "PICKUP", "BODY_SHELL")):
            if obj.name.startswith("WGT-") or obj.type in {"CAMERA", "LIGHT"}:
                continue
            guitar_objects[obj.name] = object_record(obj)

    record = {
        "source": str(SOURCE.relative_to(ROOT)),
        "objects": {
            name: object_record(obj)
            for name in object_names
            if (obj := bpy.data.objects.get(name)) is not None
        },
        "rigs": rigs,
        "guitar_objects": guitar_objects,
        "scene_camera": bpy.context.scene.camera.name if bpy.context.scene.camera else None,
        "scene_engine": bpy.context.scene.render.engine,
    }
    print("V300_INTEGRATION_LANDMARKS=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
