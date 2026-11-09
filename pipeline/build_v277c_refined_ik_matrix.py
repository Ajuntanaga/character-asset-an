"""Refine V277B IK planes, bend ranges, foot placement, and guitar wrists."""

from pathlib import Path
import hashlib
import json
import math

import bpy
from mathutils import Matrix, Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v277b_ik_target_matrix" / "Character_An_ik_target_matrix_v277b.blend"
STAGE = ROOT / "production_v277c_refined_ik_matrix"
OUTPUT = STAGE / "Character_An_refined_ik_matrix_v277c.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"
BODY = "V211_BODY_NEUTRAL"
RIG = "V239_CLEAN_CHARACTER_RIG"


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            digest.update(block)
    return digest.hexdigest()


def point_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def world_matrix(rig, bone):
    return rig.matrix_world @ bone.matrix


def apply_world_matrix(rig, bone, matrix):
    bone.matrix = rig.matrix_world.inverted() @ matrix


def with_translation(matrix, location):
    result = matrix.copy()
    result.translation = location
    return result


def direction_matrix(location, direction):
    result = direction.normalized().to_track_quat("Y", "Z").to_matrix().to_4x4()
    result.translation = location
    return result


def rotated_at_location(matrix, location, rotations):
    orientation = matrix.to_3x3().to_4x4()
    for angle, axis in rotations:
        orientation = Matrix.Rotation(angle, 4, axis.normalized()) @ orientation
    return Matrix.Translation(location) @ orientation


def pose_point_world(rig, name):
    return rig.matrix_world @ rig.pose.bones[name].head


def evaluated_positions(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    try:
        return [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    finally:
        evaluated.to_mesh_clear()


def key_transform(bone, frame):
    bone.rotation_mode = "QUATERNION"
    bone.keyframe_insert(data_path="location", frame=frame, group=bone.name)
    bone.keyframe_insert(data_path="rotation_quaternion", frame=frame, group=bone.name)
    bone.keyframe_insert(data_path="scale", frame=frame, group=bone.name)


def main():
    if Path(bpy.data.filepath).resolve() != SOURCE.resolve():
        raise RuntimeError(f"Open V277B first: {SOURCE}")
    for folder in (STAGE, RENDERS, AUDIT):
        folder.mkdir(parents=True, exist_ok=True)

    scene = bpy.context.scene
    body = bpy.data.objects[BODY]
    rig = bpy.data.objects[RIG]
    pose = rig.pose.bones
    target_names = [f"{name}.{side}" for side in ("L", "R") for name in ("hand_ik", "upper_arm_ik_target", "foot_ik", "thigh_ik_target")]

    scene.frame_set(1)
    bpy.context.view_layer.update()
    neutral = {name: world_matrix(rig, pose[name]).copy() for name in target_names}
    anatomy = {
        side: {
            "shoulder": pose_point_world(rig, f"DEF-upper_arm.{side}"),
            "knee": pose_point_world(rig, f"DEF-shin.{side}"),
            "hip": pose_point_world(rig, f"DEF-thigh.{side}"),
        }
        for side in ("L", "R")
    }
    front = Vector((0.0, -1.0, 0.0))
    up = Vector((0.0, 0.0, 1.0))

    def base_targets():
        return {name: matrix.copy() for name, matrix in neutral.items()}

    poses = {1: ("neutral", base_targets())}
    raised = base_targets()
    for side in ("L", "R"):
        shoulder = anatomy[side]["shoulder"]
        hand = neutral[f"hand_ik.{side}"].translation
        side_vector = Vector((hand.x - shoulder.x, hand.y - shoulder.y, 0.0)).normalized()
        length = (hand - shoulder).length
        hand_target = shoulder + (side_vector * 0.56 + up * 0.80 + front * 0.05).normalized() * length * 0.97
        pole_target = shoulder.lerp(hand_target, 0.50) + front * 0.14 + side_vector * 0.06
        raised[f"hand_ik.{side}"] = with_translation(neutral[f"hand_ik.{side}"], hand_target)
        raised[f"upper_arm_ik_target.{side}"] = with_translation(neutral[f"upper_arm_ik_target.{side}"], pole_target)
    poses[10] = ("shoulder_elevation", raised)

    for frame, side, label in ((20, "L", "left_elbow_flex"), (30, "R", "right_elbow_flex")):
        targets = base_targets()
        shoulder = anatomy[side]["shoulder"]
        hand = neutral[f"hand_ik.{side}"].translation
        side_vector = Vector((hand.x - shoulder.x, hand.y - shoulder.y, 0.0)).normalized()
        length = (hand - shoulder).length
        direction = (side_vector * 0.58 + front * 0.45 + Vector((0.0, 0.0, -0.42))).normalized()
        hand_target = shoulder + direction * length * 0.78
        pole_target = shoulder.lerp(hand_target, 0.52) + front * 0.16 + side_vector * 0.12
        targets[f"hand_ik.{side}"] = with_translation(neutral[f"hand_ik.{side}"], hand_target)
        targets[f"upper_arm_ik_target.{side}"] = with_translation(neutral[f"upper_arm_ik_target.{side}"], pole_target)
        poses[frame] = (label, targets)

    wrists = base_targets()
    for side, sign in (("L", 1.0), ("R", -1.0)):
        name = f"hand_ik.{side}"
        shoulder = anatomy[side]["shoulder"]
        location = neutral[name].translation
        forearm = (location - shoulder).normalized()
        transverse = neutral[name].to_3x3().col[0].normalized()
        wrists[name] = rotated_at_location(neutral[name], location, [(math.radians(14.0) * sign, transverse), (math.radians(18.0) * sign, forearm)])
    poses[40] = ("wrist_flex_pronation", wrists)

    knees = base_targets()
    for side in ("L", "R"):
        foot_name = f"foot_ik.{side}"
        pole_name = f"thigh_ik_target.{side}"
        hip = anatomy[side]["hip"]
        foot = neutral[foot_name].translation
        reach = foot - hip
        target = hip + reach * 0.96 + front * 0.035
        outward = Vector((0.035 if side == "L" else -0.035, 0.0, 0.0))
        knees[foot_name] = with_translation(neutral[foot_name], target)
        knees[pole_name] = with_translation(neutral[pole_name], anatomy[side]["knee"] + front * 0.20 + outward)
    poses[50] = ("knee_flex", knees)

    ankles = base_targets()
    for side, angle in (("L", math.radians(18.0)), ("R", math.radians(-14.0))):
        name = f"foot_ik.{side}"
        axis = neutral[name].to_3x3().col[0].normalized()
        ankles[name] = rotated_at_location(neutral[name], neutral[name].translation, [(angle, axis)])
    poses[60] = ("ankle_flexion", ankles)

    guitar = base_targets()
    guitar_data = {
        "L": (Vector((0.195, -0.345, 1.340)), Vector((0.53, 0.04, 1.245)), Vector((0.060, -0.045, 0.030))),
        "R": (Vector((-0.145, -0.345, 1.260)), Vector((-0.50, 0.04, 1.185)), Vector((0.070, -0.040, -0.060))),
    }
    for side, (hand_target, pole_target, direction) in guitar_data.items():
        guitar[f"hand_ik.{side}"] = direction_matrix(hand_target, direction)
        guitar[f"upper_arm_ik_target.{side}"] = with_translation(neutral[f"upper_arm_ik_target.{side}"], pole_target)
    poses[70] = ("guitar_safe_upper_body", guitar)
    poses[80] = ("neutral_return", base_targets())

    for frame, (_, targets) in poses.items():
        scene.frame_set(frame)
        for name in target_names:
            apply_world_matrix(rig, pose[name], targets[name])
            key_transform(pose[name], frame)
        bpy.context.view_layer.update()

    camera = bpy.data.objects["V277B_ACCEPTANCE_CAMERA"]
    scene.render.resolution_x = 800
    scene.render.resolution_y = 900
    jobs = [
        (1, "neutral_front", "full"),
        (10, "shoulder_front", "upper"),
        (10, "shoulder_3q", "threeq"),
        (20, "left_elbow", "upper"),
        (30, "right_elbow", "upper"),
        (40, "wrists", "upper"),
        (50, "knees", "lower"),
        (60, "ankles", "lower"),
        (70, "guitar_front", "full"),
        (70, "guitar_3q", "threeq"),
        (80, "neutral_return", "full"),
    ]
    renders = []
    for frame, label, view in jobs:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        if view == "full":
            camera.location = Vector((0.0, -3.45, 1.02)); camera.data.lens = 68.0; point_at(camera, Vector((0.0, 0.0, 0.98)))
        elif view == "threeq":
            camera.location = Vector((-2.40, -2.65, 1.20)); camera.data.lens = 72.0; point_at(camera, Vector((0.0, 0.0, 1.02)))
        elif view == "upper":
            camera.location = Vector((0.0, -2.35, 1.34)); camera.data.lens = 82.0; point_at(camera, Vector((0.0, -0.02, 1.30)))
        else:
            feet = (pose_point_world(rig, "DEF-foot.L") + pose_point_world(rig, "DEF-foot.R")) * 0.5
            camera.location = feet + Vector((-0.65, -2.20, 0.62)); camera.data.lens = 72.0; point_at(camera, feet + Vector((0.0, 0.0, 0.40)))
        scene.camera = camera
        path = RENDERS / f"v277c_{label}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        renders.append(str(path.relative_to(ROOT)))

    scene.frame_set(1)
    bpy.context.view_layer.update()
    neutral_vertices = evaluated_positions(body)
    metrics = {}
    for frame, (label, _) in poses.items():
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        vertices = evaluated_positions(body)
        metrics[label] = {
            "frame": frame,
            "max_vertex_displacement_m": round(max((a - b).length for a, b in zip(vertices, neutral_vertices)), 6),
            "hands": {side: list(pose_point_world(rig, f"DEF-hand.{side}")) for side in ("L", "R")},
            "feet": {side: list(pose_point_world(rig, f"DEF-foot.{side}")) for side in ("L", "R")},
        }
    neutral_error = metrics["neutral_return"]["max_vertex_displacement_m"]
    if neutral_error > 1e-6:
        raise RuntimeError(f"Neutral return drifted by {neutral_error} m")

    scene.frame_set(1)
    scene["V277C_STATUS"] = "REFINED_IK_MATRIX_VISUAL_REVIEW_REQUIRED"
    scene["V277C_NEUTRAL_RETURN_ERROR_M"] = neutral_error
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v277c-refined-ik-target-matrix-v1",
        "status": "BUILT_VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha256(SOURCE)},
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha256(OUTPUT)},
        "neutral_return_error_m": neutral_error,
        "refinements": ["reduced arm-pole depth", "moderated elbow and wrist ranges", "near-planted knee test", "explicit guitar hand orientations"],
        "poses": metrics,
        "renders": renders,
    }
    (AUDIT / "v277c_refined_ik_matrix.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V277C_REFINED_IK_MATRIX_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
