"""Pose the clean V239 Rigify arms to the accepted guitar contact regions."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import bpy
from mathutils import Euler, Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v244_guitar_integration" / "Character_An_guitar_integration_v244.blend"
STAGE = ROOT / "production_v245_arm_performance_pose"
OUTPUT = STAGE / "Character_An_arm_performance_v245.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"
RIG_NAME = "V239_CLEAN_CHARACTER_RIG"

FRETTING_HAND_TARGET = Vector((0.195, -0.345, 1.340))
PICKING_HAND_TARGET = Vector((-0.145, -0.345, 1.260))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def place_control(bone: bpy.types.PoseBone, target: Vector, rotation: tuple[float, float, float]) -> None:
    transform = Euler(rotation, "XYZ").to_matrix().to_4x4()
    transform.translation = target
    bone.matrix = transform


def place_control_direction(bone: bpy.types.PoseBone, target: Vector, direction: Vector) -> None:
    transform = direction.normalized().to_track_quat("Y", "Z").to_matrix().to_4x4()
    transform.translation = target
    bone.matrix = transform


def point_at(obj: bpy.types.Object, target: Vector) -> None:
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def main() -> None:
    if Path(bpy.data.filepath).resolve() != SOURCE.resolve():
        raise RuntimeError(f"Open V244 first: {SOURCE}")
    STAGE.mkdir(parents=True, exist_ok=True)
    RENDERS.mkdir(parents=True, exist_ok=True)
    AUDIT.mkdir(parents=True, exist_ok=True)
    rig = bpy.data.objects[RIG_NAME]
    pose = rig.pose.bones
    for side in ("L", "R"):
        parent = pose[f"upper_arm_parent.{side}"]
        parent["IK_FK"] = 0.0
        parent["IK_Stretch"] = 0.03

    place_control_direction(pose["hand_ik.L"], FRETTING_HAND_TARGET, Vector((0.060, -0.045, 0.030)))
    place_control_direction(pose["hand_ik.R"], PICKING_HAND_TARGET, Vector((0.070, -0.040, -0.060)))
    place_control(pose["upper_arm_ik_target.L"], Vector((0.53, -0.32, 1.260)), (0.0, 0.0, 0.0))
    place_control(pose["upper_arm_ik_target.R"], Vector((-0.50, -0.30, 1.205)), (0.0, 0.0, 0.0))
    bpy.context.view_layer.update()

    action = bpy.data.actions.get("V245_GUITAR_PERFORMANCE_POSE") or bpy.data.actions.new("V245_GUITAR_PERFORMANCE_POSE")
    rig.animation_data_create()
    rig.animation_data.action = action
    for bone_name in ("hand_ik.L", "hand_ik.R", "upper_arm_ik_target.L", "upper_arm_ik_target.R"):
        bone = pose[bone_name]
        bone.keyframe_insert(data_path="location", frame=1, group=bone_name)
        bone.keyframe_insert(data_path="rotation_quaternion" if bone.rotation_mode == "QUATERNION" else "rotation_euler", frame=1, group=bone_name)
    for side in ("L", "R"):
        parent = pose[f"upper_arm_parent.{side}"]
        parent.keyframe_insert(data_path='["IK_FK"]', frame=1, group=parent.name)
        parent.keyframe_insert(data_path='["IK_Stretch"]', frame=1, group=parent.name)
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.look = "AgX - Medium High Contrast"
    camera = bpy.data.objects["CAM_V211_FRONT"]
    camera.data.type = "PERSP"
    views = {
        "full_front": (Vector((0.0, -3.75, 1.00)), Vector((0.0, 0.0, 1.00)), 66.0, (900, 1000)),
        "performance": (Vector((-1.70, -2.85, 1.18)), Vector((0.0, -0.03, 1.16)), 72.0, (1100, 900)),
        "arms": (Vector((-0.70, -2.05, 1.30)), Vector((0.03, -0.04, 1.31)), 82.0, (1150, 850)),
    }
    render_records = {}
    for label, (location, target_point, lens, resolution) in views.items():
        camera.location = location
        camera.data.lens = lens
        point_at(camera, target_point)
        scene.camera = camera
        scene.render.resolution_x, scene.render.resolution_y = resolution
        scene.render.resolution_percentage = 100
        path = RENDERS / f"v245_{label}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        render_records[label] = {"path": str(path.relative_to(ROOT)), "sha256": sha256(path)}

    hand_positions = {
        side: [round(float(value), 7) for value in pose[f"DEF-hand.{side}"].matrix.translation]
        for side in ("L", "R")
    }
    scene["V245_STATUS"] = "CLEAN_RIG_TWO_ARM_GUITAR_PERFORMANCE_POSE"
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v245-arm-performance-pose-v1",
        "status": "BUILT_VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha256(SOURCE)},
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha256(OUTPUT)},
        "rig": RIG_NAME,
        "action": action.name,
        "fretting_hand_target": list(FRETTING_HAND_TARGET),
        "picking_hand_target": list(PICKING_HAND_TARGET),
        "def_hand_positions": hand_positions,
        "renders": render_records,
    }
    (AUDIT / "v245_manifest.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("V245_ARM_PERFORMANCE_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
