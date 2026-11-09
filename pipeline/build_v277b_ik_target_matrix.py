"""Build an IK-target body deformation matrix from the accepted V239 rig."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import bpy
from mathutils import Matrix, Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v239_clean_auto_rig" / "Character_An_clean_auto_rig_v239.blend"
STAGE = ROOT / "production_v277b_ik_target_matrix"
OUTPUT = STAGE / "Character_An_ik_target_matrix_v277b.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"
BODY = "V211_BODY_NEUTRAL"
RIG = "V239_CLEAN_CHARACTER_RIG"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def point_at(obj: bpy.types.Object, target: Vector) -> None:
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def make_camera(name: str) -> bpy.types.Object:
    obj = bpy.data.objects.get(name)
    if obj is None:
        data = bpy.data.cameras.new(f"{name}_DATA")
        obj = bpy.data.objects.new(name, data)
        bpy.context.scene.collection.objects.link(obj)
    obj.data.type = "PERSP"
    return obj


def set_camera(obj: bpy.types.Object, location: Vector, target: Vector, lens: float) -> None:
    obj.location = location
    obj.data.lens = lens
    point_at(obj, target)


def world_matrix(rig: bpy.types.Object, bone: bpy.types.PoseBone) -> Matrix:
    return rig.matrix_world @ bone.matrix


def apply_world_matrix(rig: bpy.types.Object, bone: bpy.types.PoseBone, target_world: Matrix) -> None:
    bone.matrix = rig.matrix_world.inverted() @ target_world


def with_translation(matrix: Matrix, location: Vector) -> Matrix:
    result = matrix.copy()
    result.translation = location
    return result


def rotated_at_location(matrix: Matrix, location: Vector, rotations: list[tuple[float, Vector]]) -> Matrix:
    orientation = matrix.to_3x3().to_4x4()
    for angle, axis in rotations:
        orientation = Matrix.Rotation(angle, 4, axis.normalized()) @ orientation
    return Matrix.Translation(location) @ orientation


def evaluated_positions(obj: bpy.types.Object) -> list[Vector]:
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    try:
        return [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    finally:
        evaluated.to_mesh_clear()


def pose_point_world(rig: bpy.types.Object, name: str, endpoint: str = "head") -> Vector:
    bone = rig.pose.bones[name]
    point = bone.head if endpoint == "head" else bone.tail
    return rig.matrix_world @ point


def key_transform(bone: bpy.types.PoseBone, frame: int) -> None:
    bone.rotation_mode = "QUATERNION"
    bone.keyframe_insert(data_path="location", frame=frame, group=bone.name)
    bone.keyframe_insert(data_path="rotation_quaternion", frame=frame, group=bone.name)
    bone.keyframe_insert(data_path="scale", frame=frame, group=bone.name)


def main() -> None:
    if Path(bpy.data.filepath).resolve() != SOURCE.resolve():
        raise RuntimeError(f"Open the V239 source first: {SOURCE}")
    for folder in (STAGE, RENDERS, AUDIT):
        folder.mkdir(parents=True, exist_ok=True)

    scene = bpy.context.scene
    body = bpy.data.objects[BODY]
    rig = bpy.data.objects[RIG]
    pose = rig.pose.bones
    modifier = next((item for item in body.modifiers if item.type == "ARMATURE" and item.object == rig), None)
    if modifier is None:
        raise RuntimeError("V239 body is not bound to its clean Rigify armature")

    required = [
        f"{name}.{side}"
        for side in ("L", "R")
        for name in ("hand_ik", "upper_arm_ik_target", "foot_ik", "thigh_ik_target", "upper_arm_parent", "thigh_parent")
    ]
    required += [
        f"DEF-{name}.{side}"
        for side in ("L", "R")
        for name in ("upper_arm", "forearm", "hand", "thigh", "shin", "foot")
    ]
    missing = [name for name in required if pose.get(name) is None]
    if missing:
        raise RuntimeError(f"Missing V239 controls/deform bones: {missing}")

    if rig.animation_data:
        rig.animation_data_clear()
    for bone in pose:
        bone.matrix_basis.identity()
    scene.frame_set(1)
    bpy.context.view_layer.update()

    constraint_repairs = []
    for side in ("L", "R"):
        for segment in ("upper_arm", "forearm", "hand", "thigh", "shin", "foot"):
            bone = pose.get(f"ORG-{segment}.{side}")
            if bone is None:
                continue
            copies = [item for item in bone.constraints if item.type == "COPY_TRANSFORMS"]
            if len(copies) < 2:
                continue
            for index, constraint in enumerate(copies[:2]):
                try:
                    constraint.driver_remove("influence")
                except (TypeError, RuntimeError):
                    pass
                constraint.influence = 0.0 if index == 0 else 1.0
            constraint_repairs.append({
                "bone": bone.name,
                "fk_constraint": copies[0].name,
                "ik_constraint": copies[1].name,
                "influences": [copies[0].influence, copies[1].influence],
            })
    if len(constraint_repairs) != 12:
        raise RuntimeError(f"Expected 12 IK constraint repairs, got {len(constraint_repairs)}")

    parents = [pose[f"{kind}.{side}"] for kind in ("upper_arm_parent", "thigh_parent") for side in ("L", "R")]
    for parent in parents:
        parent["IK_FK"] = 0.0
        parent["IK_Stretch"] = 0.0
    bpy.context.view_layer.update()

    target_names = [f"{name}.{side}" for side in ("L", "R") for name in ("hand_ik", "upper_arm_ik_target", "foot_ik", "thigh_ik_target")]
    neutral = {name: world_matrix(rig, pose[name]).copy() for name in target_names}
    anatomy = {}
    for side in ("L", "R"):
        anatomy[side] = {
            "shoulder": pose_point_world(rig, f"DEF-upper_arm.{side}"),
            "elbow": pose_point_world(rig, f"DEF-forearm.{side}"),
            "hand": pose_point_world(rig, f"DEF-hand.{side}"),
            "hip": pose_point_world(rig, f"DEF-thigh.{side}"),
            "knee": pose_point_world(rig, f"DEF-shin.{side}"),
            "foot": pose_point_world(rig, f"DEF-foot.{side}"),
        }

    front = Vector((0.0, -1.0, 0.0))
    up = Vector((0.0, 0.0, 1.0))
    poses: dict[int, tuple[str, dict[str, Matrix]]] = {}

    def base_targets() -> dict[str, Matrix]:
        return {name: matrix.copy() for name, matrix in neutral.items()}

    poses[1] = ("neutral", base_targets())

    shoulder_targets = base_targets()
    for side in ("L", "R"):
        shoulder = anatomy[side]["shoulder"]
        neutral_hand = neutral[f"hand_ik.{side}"].translation
        side_vector = Vector((neutral_hand.x - shoulder.x, neutral_hand.y - shoulder.y, 0.0)).normalized()
        length = (neutral_hand - shoulder).length
        direction = (side_vector * 0.55 + up * 0.78 + front * 0.12).normalized()
        hand_target = shoulder + direction * length * 0.90
        pole_target = shoulder.lerp(hand_target, 0.48) + front * 0.55 + side_vector * 0.08
        shoulder_targets[f"hand_ik.{side}"] = with_translation(neutral[f"hand_ik.{side}"], hand_target)
        shoulder_targets[f"upper_arm_ik_target.{side}"] = with_translation(neutral[f"upper_arm_ik_target.{side}"], pole_target)
    poses[10] = ("shoulder_elevation", shoulder_targets)

    for frame, active_side, label in ((20, "L", "left_elbow_flex"), (30, "R", "right_elbow_flex")):
        targets = base_targets()
        shoulder = anatomy[active_side]["shoulder"]
        neutral_hand = neutral[f"hand_ik.{active_side}"].translation
        side_vector = Vector((neutral_hand.x - shoulder.x, neutral_hand.y - shoulder.y, 0.0)).normalized()
        length = (neutral_hand - shoulder).length
        direction = (side_vector * 0.58 + front * 0.70 + Vector((0.0, 0.0, -0.18))).normalized()
        hand_target = shoulder + direction * length * 0.63
        pole_target = shoulder.lerp(hand_target, 0.46) + front * 0.52 + side_vector * 0.10
        targets[f"hand_ik.{active_side}"] = with_translation(neutral[f"hand_ik.{active_side}"], hand_target)
        targets[f"upper_arm_ik_target.{active_side}"] = with_translation(neutral[f"upper_arm_ik_target.{active_side}"], pole_target)
        poses[frame] = (label, targets)

    wrist_targets = base_targets()
    for side, sign in (("L", 1.0), ("R", -1.0)):
        hand_name = f"hand_ik.{side}"
        shoulder = anatomy[side]["shoulder"]
        location = neutral[hand_name].translation
        forearm_axis = (location - shoulder).normalized()
        transverse = neutral[hand_name].to_3x3().col[0].normalized()
        wrist_targets[hand_name] = rotated_at_location(
            neutral[hand_name],
            location,
            [(math.radians(28.0) * sign, transverse), (math.radians(34.0) * sign, forearm_axis)],
        )
    poses[40] = ("wrist_flex_pronation", wrist_targets)

    knee_targets = base_targets()
    for side in ("L", "R"):
        foot_name = f"foot_ik.{side}"
        pole_name = f"thigh_ik_target.{side}"
        hip = anatomy[side]["hip"]
        foot = neutral[foot_name].translation
        reach = foot - hip
        shortened = hip + reach * 0.83 + front * 0.045
        outward = Vector((0.06 if side == "L" else -0.06, 0.0, 0.0))
        pole_target = anatomy[side]["knee"] + front * 0.50 + outward
        knee_targets[foot_name] = with_translation(neutral[foot_name], shortened)
        knee_targets[pole_name] = with_translation(neutral[pole_name], pole_target)
    poses[50] = ("knee_flex", knee_targets)

    ankle_targets = base_targets()
    for side, angle in (("L", math.radians(24.0)), ("R", math.radians(-18.0))):
        name = f"foot_ik.{side}"
        transverse = neutral[name].to_3x3().col[0].normalized()
        ankle_targets[name] = rotated_at_location(neutral[name], neutral[name].translation, [(angle, transverse)])
    poses[60] = ("ankle_flexion", ankle_targets)

    guitar_targets = base_targets()
    guitar_positions = {
        "L": (Vector((0.195, -0.345, 1.340)), Vector((0.53, -0.32, 1.260))),
        "R": (Vector((-0.145, -0.345, 1.260)), Vector((-0.50, -0.30, 1.205))),
    }
    for side, (hand_target, pole_target) in guitar_positions.items():
        hand_name = f"hand_ik.{side}"
        forearm_axis = (hand_target - anatomy[side]["shoulder"]).normalized()
        transverse = neutral[hand_name].to_3x3().col[0].normalized()
        guitar_targets[hand_name] = rotated_at_location(
            neutral[hand_name], hand_target, [(math.radians(18.0 if side == "L" else -12.0), transverse), (math.radians(18.0), forearm_axis)]
        )
        guitar_targets[f"upper_arm_ik_target.{side}"] = with_translation(neutral[f"upper_arm_ik_target.{side}"], pole_target)
    poses[70] = ("guitar_safe_upper_body", guitar_targets)
    poses[80] = ("neutral_return", base_targets())

    action = bpy.data.actions.new("V277B_IK_TARGET_DEFORMATION_MATRIX")
    rig.animation_data_create()
    rig.animation_data.action = action
    for frame, (_, targets) in poses.items():
        scene.frame_set(frame)
        for parent in parents:
            parent["IK_FK"] = 0.0
            parent["IK_Stretch"] = 0.0
            parent.keyframe_insert(data_path='["IK_FK"]', frame=frame, group=parent.name)
            parent.keyframe_insert(data_path='["IK_Stretch"]', frame=frame, group=parent.name)
        for name in target_names:
            apply_world_matrix(rig, pose[name], targets[name])
            key_transform(pose[name], frame)
        bpy.context.view_layer.update()

    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 800
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.frame_start = 1
    scene.frame_end = 80
    camera = make_camera("V277B_ACCEPTANCE_CAMERA")

    jobs = [
        (1, "neutral_front", "full_front"),
        (10, "shoulder_elevation_front", "upper_front"),
        (10, "shoulder_elevation_3q", "full_3q"),
        (20, "left_elbow_close", "left_elbow"),
        (30, "right_elbow_close", "right_elbow"),
        (40, "wrist_flex_front", "upper_front"),
        (50, "knee_flex_lower", "lower_3q"),
        (60, "ankle_flex_lower", "lower_front"),
        (70, "guitar_safe_front", "full_front"),
        (70, "guitar_safe_3q", "full_3q"),
        (80, "neutral_return_front", "full_front"),
    ]
    rendered = []
    for frame, label, view in jobs:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        if view == "full_front":
            set_camera(camera, Vector((0.0, -3.45, 1.02)), Vector((0.0, 0.0, 0.98)), 68.0)
        elif view == "full_3q":
            set_camera(camera, Vector((-2.40, -2.65, 1.20)), Vector((0.0, 0.0, 1.02)), 72.0)
        elif view == "upper_front":
            set_camera(camera, Vector((0.0, -2.25, 1.35)), Vector((0.0, -0.02, 1.32)), 86.0)
        elif view in ("left_elbow", "right_elbow"):
            side = "L" if view == "left_elbow" else "R"
            shoulder = pose_point_world(rig, f"DEF-upper_arm.{side}")
            elbow = pose_point_world(rig, f"DEF-forearm.{side}")
            target = shoulder.lerp(elbow, 0.58)
            offset_x = 0.48 if side == "L" else -0.48
            set_camera(camera, target + Vector((offset_x, -1.35, 0.10)), target, 102.0)
        elif view == "lower_3q":
            target = (pose_point_world(rig, "DEF-shin.L") + pose_point_world(rig, "DEF-shin.R")) * 0.5
            set_camera(camera, target + Vector((-1.35, -1.85, 0.38)), target, 78.0)
        elif view == "lower_front":
            feet = (pose_point_world(rig, "DEF-foot.L") + pose_point_world(rig, "DEF-foot.R")) * 0.5
            set_camera(camera, feet + Vector((0.0, -2.10, 0.40)), feet + Vector((0.0, 0.0, 0.22)), 74.0)
        path = RENDERS / f"v277b_{label}.png"
        scene.camera = camera
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        rendered.append(str(path.relative_to(ROOT)))

    scene.frame_set(1)
    bpy.context.view_layer.update()
    neutral_vertices = evaluated_positions(body)
    pose_metrics = {}
    for frame, (label, targets) in poses.items():
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        current = evaluated_positions(body)
        maximum = max((a - b).length for a, b in zip(current, neutral_vertices))
        pose_metrics[label] = {
            "frame": frame,
            "max_vertex_displacement_m": round(maximum, 6),
            "def_hand_world": {side: list(pose_point_world(rig, f"DEF-hand.{side}")) for side in ("L", "R")},
            "def_foot_world": {side: list(pose_point_world(rig, f"DEF-foot.{side}")) for side in ("L", "R")},
        }
    neutral_return_error = pose_metrics["neutral_return"]["max_vertex_displacement_m"]
    if neutral_return_error > 1e-6:
        raise RuntimeError(f"Neutral return drifted by {neutral_return_error} m")

    scene.frame_set(1)
    scene["V277B_STATUS"] = "IK_TARGET_MATRIX_VISUAL_REVIEW_REQUIRED"
    scene["V277B_NEUTRAL_RETURN_ERROR_M"] = neutral_return_error
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v277b-ik-target-deformation-matrix-v1",
        "status": "BUILT_VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha256(SOURCE)},
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha256(OUTPUT)},
        "body": BODY,
        "rig": RIG,
        "action": action.name,
        "armature_modifier": modifier.name,
        "preserve_volume": modifier.use_deform_preserve_volume,
        "limb_mode": "IK constraints forced authoritative; world-space hand, foot, and pole target matrices",
        "constraint_repairs": constraint_repairs,
        "neutral_return_error_m": neutral_return_error,
        "poses": pose_metrics,
        "renders": rendered,
    }
    (AUDIT / "v277b_ik_target_matrix.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("V277B_IK_TARGET_MATRIX_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
