"""Build a clean-body Rigify deformation acceptance matrix from V239."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v239_clean_auto_rig" / "Character_An_clean_auto_rig_v239.blend"
STAGE = ROOT / "production_v277a_deformation_matrix"
OUTPUT = STAGE / "Character_An_deformation_matrix_v277a.blend"
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


def camera(name: str, location: tuple[float, float, float], target: tuple[float, float, float], lens: float) -> bpy.types.Object:
    obj = bpy.data.objects.get(name)
    if obj is None:
        data = bpy.data.cameras.new(f"{name}_DATA")
        obj = bpy.data.objects.new(name, data)
        bpy.context.scene.collection.objects.link(obj)
    obj.location = Vector(location)
    obj.data.lens = lens
    point_at(obj, Vector(target))
    return obj


def evaluated_positions(obj: bpy.types.Object) -> list[Vector]:
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    try:
        matrix = evaluated.matrix_world
        return [matrix @ vertex.co for vertex in mesh.vertices]
    finally:
        evaluated.to_mesh_clear()


def render(scene: bpy.types.Scene, cam: bpy.types.Object, path: Path) -> None:
    scene.camera = cam
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def main() -> None:
    if Path(bpy.data.filepath).resolve() != SOURCE.resolve():
        raise RuntimeError(f"Open the V239 source first: {SOURCE}")
    STAGE.mkdir(parents=True, exist_ok=True)
    RENDERS.mkdir(parents=True, exist_ok=True)
    AUDIT.mkdir(parents=True, exist_ok=True)

    scene = bpy.context.scene
    body = bpy.data.objects[BODY]
    rig = bpy.data.objects[RIG]
    modifier = next((item for item in body.modifiers if item.type == "ARMATURE" and item.object == rig), None)
    if modifier is None:
        raise RuntimeError("V239 body is not bound to the clean Rigify armature")

    # V239's generated ORG limb chains saved with both FK and IK copy-transform
    # constraints at full influence. The last (IK) constraint therefore erased
    # every FK edit. Repair only this output branch by removing the broken
    # influence drivers and selecting the first/FK constraint explicitly.
    constraint_repairs = []
    for side in ("L", "R"):
        for segment in ("upper_arm", "forearm", "hand", "thigh", "shin", "foot"):
            bone = rig.pose.bones.get(f"ORG-{segment}.{side}")
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
                constraint.influence = 1.0 if index == 0 else 0.0
            constraint_repairs.append({
                "bone": bone.name,
                "fk_constraint": copies[0].name,
                "ik_constraint": copies[1].name,
            })
    if len(constraint_repairs) < 8:
        raise RuntimeError(f"Incomplete FK constraint repair: {constraint_repairs}")

    # V239 was saved after its proof pose. Remove that pose and any old action
    # before making the controlled matrix so frame 1 is an exact neutral base.
    if rig.animation_data:
        rig.animation_data_clear()
    for bone in rig.pose.bones:
        bone.matrix_basis.identity()

    # This generated Rigify rig uses IK_FK=0 for the FK deform chain. The
    # matrix is authored on FK controls, so make that state explicit and key it at
    # every proof frame rather than relying on an implicit UI setting.
    limb_parents = [
        rig.pose.bones[f"{prefix}.{side}"]
        for prefix in ("upper_arm_parent", "thigh_parent")
        for side in ("L", "R")
    ]
    for parent in limb_parents:
        parent["IK_FK"] = 0.0
        parent["IK_Stretch"] = 0.0

    degrees = math.radians
    poses: dict[int, tuple[str, dict[str, tuple[float, float, float]]]] = {
        1: ("neutral", {}),
        10: ("shoulder_elevation", {
            "upper_arm_fk.L": (degrees(-18), degrees(-12), degrees(-78)),
            "upper_arm_fk.R": (degrees(-18), degrees(12), degrees(78)),
        }),
        20: ("left_elbow_flex", {
            "upper_arm_fk.L": (degrees(-12), degrees(-8), degrees(-42)),
            "forearm_fk.L": (degrees(2), degrees(-10), degrees(-112)),
        }),
        30: ("right_elbow_flex", {
            "upper_arm_fk.R": (degrees(-12), degrees(8), degrees(42)),
            "forearm_fk.R": (degrees(2), degrees(10), degrees(112)),
        }),
        40: ("wrist_flex_pronation", {
            "upper_arm_fk.L": (degrees(-8), degrees(-8), degrees(-34)),
            "forearm_fk.L": (degrees(0), degrees(-8), degrees(-72)),
            "hand_fk.L": (degrees(28), degrees(-24), degrees(-12)),
            "upper_arm_fk.R": (degrees(-8), degrees(8), degrees(34)),
            "forearm_fk.R": (degrees(0), degrees(8), degrees(72)),
            "hand_fk.R": (degrees(-28), degrees(24), degrees(12)),
        }),
        50: ("lower_body_bend", {
            "spine_fk.002": (degrees(10), degrees(0), degrees(0)),
            "thigh_fk.L": (degrees(42), degrees(0), degrees(-8)),
            "shin_fk.L": (degrees(-78), degrees(0), degrees(0)),
            "thigh_fk.R": (degrees(24), degrees(0), degrees(8)),
            "shin_fk.R": (degrees(-52), degrees(0), degrees(0)),
        }),
        60: ("ankle_bend", {
            "thigh_fk.L": (degrees(12), degrees(0), degrees(-3)),
            "shin_fk.L": (degrees(-28), degrees(0), degrees(0)),
            "foot_fk.L": (degrees(28), degrees(0), degrees(0)),
            "thigh_fk.R": (degrees(12), degrees(0), degrees(3)),
            "shin_fk.R": (degrees(-28), degrees(0), degrees(0)),
            "foot_fk.R": (degrees(-18), degrees(0), degrees(0)),
        }),
        70: ("torso_twist", {
            "spine_fk.001": (degrees(0), degrees(5), degrees(-10)),
            "spine_fk.002": (degrees(0), degrees(8), degrees(-18)),
            "upper_arm_fk.L": (degrees(-10), degrees(-6), degrees(-26)),
            "upper_arm_fk.R": (degrees(-10), degrees(6), degrees(26)),
        }),
        80: ("guitar_safe_upper_body", {
            "upper_arm_fk.L": (degrees(-10), degrees(-8), degrees(-22)),
            "forearm_fk.L": (degrees(0), degrees(-10), degrees(-58)),
            "upper_arm_fk.R": (degrees(-8), degrees(10), degrees(18)),
            "forearm_fk.R": (degrees(0), degrees(8), degrees(48)),
            "thigh_fk.L": (degrees(6), degrees(0), degrees(-4)),
            "shin_fk.L": (degrees(-12), degrees(0), degrees(0)),
            "spine_fk.002": (degrees(0), degrees(5), degrees(-4)),
        }),
        90: ("neutral_return", {}),
    }
    control_names = sorted({name for _, values in poses.values() for name in values})
    missing = [name for name in control_names if rig.pose.bones.get(name) is None]
    if missing:
        raise RuntimeError(f"Missing Rigify controls: {missing}")

    action = bpy.data.actions.new("V277A_BODY_DEFORMATION_MATRIX")
    rig.animation_data_create()
    rig.animation_data.action = action
    for frame, (_, rotations) in poses.items():
        scene.frame_set(frame)
        for parent in limb_parents:
            parent["IK_FK"] = 0.0
            parent["IK_Stretch"] = 0.0
            parent.keyframe_insert(data_path='["IK_FK"]', frame=frame, group=parent.name)
            parent.keyframe_insert(data_path='["IK_Stretch"]', frame=frame, group=parent.name)
        for name in control_names:
            bone = rig.pose.bones[name]
            bone.rotation_mode = "XYZ"
            bone.rotation_euler = rotations.get(name, (0.0, 0.0, 0.0))
            bone.keyframe_insert(data_path="rotation_euler", frame=frame, group=name)
    cams = {
        "full_front": camera("V277A_CAM_FULL_FRONT", (0.0, -3.4, 1.05), (0.0, 0.0, 0.95), 68),
        "full_3q": camera("V277A_CAM_FULL_3Q", (-2.55, -2.55, 1.2), (0.0, 0.0, 0.95), 72),
        "upper_front": camera("V277A_CAM_UPPER_FRONT", (0.0, -2.1, 1.35), (0.0, 0.0, 1.32), 92),
        "left_joint": camera("V277A_CAM_LEFT_JOINT", (0.72, -1.55, 1.27), (0.27, 0.0, 1.25), 110),
        "right_joint": camera("V277A_CAM_RIGHT_JOINT", (-0.72, -1.55, 1.27), (-0.27, 0.0, 1.25), 110),
        "lower_3q": camera("V277A_CAM_LOWER_3Q", (-1.35, -1.65, 0.55), (0.0, 0.0, 0.52), 88),
        "ankles": camera("V277A_CAM_ANKLES", (0.0, -1.25, 0.20), (0.0, 0.0, 0.18), 105),
    }
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 720
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.frame_start = 1
    scene.frame_end = 90

    jobs = [
        (1, "neutral_front", "full_front"),
        (10, "shoulder_elevation_front", "upper_front"),
        (10, "shoulder_elevation_3q", "full_3q"),
        (20, "left_elbow_close", "left_joint"),
        (30, "right_elbow_close", "right_joint"),
        (40, "wrist_flex_front", "upper_front"),
        (50, "lower_body_bend_3q", "lower_3q"),
        (60, "ankle_bend_close", "ankles"),
        (70, "torso_twist_3q", "full_3q"),
        (80, "guitar_safe_front", "full_front"),
        (90, "neutral_return_front", "full_front"),
    ]
    rendered = []
    for frame, label, cam_name in jobs:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        path = RENDERS / f"v277a_{label}.png"
        render(scene, cams[cam_name], path)
        rendered.append(str(path.relative_to(ROOT)))

    scene.frame_set(1)
    bpy.context.view_layer.update()
    neutral = evaluated_positions(body)
    pose_metrics = {}
    for frame, (label, rotations) in poses.items():
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        current = evaluated_positions(body)
        if len(current) != len(neutral):
            raise RuntimeError(f"Evaluated vertex count changed at frame {frame}")
        maximum = max((a - b).length for a, b in zip(current, neutral))
        pose_metrics[label] = {
            "frame": frame,
            "controls": {name: [round(math.degrees(value), 3) for value in rotation] for name, rotation in rotations.items()},
            "max_vertex_displacement_m": round(maximum, 6),
        }
    neutral_return_error = pose_metrics["neutral_return"]["max_vertex_displacement_m"]
    if neutral_return_error > 1e-6:
        raise RuntimeError(f"Neutral return drifted by {neutral_return_error} m")

    scene.frame_set(1)
    scene["V277A_STATUS"] = "DEFORMATION_MATRIX_VISUAL_REVIEW_REQUIRED"
    scene["V277A_NEUTRAL_RETURN_ERROR_M"] = neutral_return_error
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v277a-clean-body-deformation-matrix-v1",
        "status": "BUILT_VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha256(SOURCE)},
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha256(OUTPUT)},
        "body": BODY,
        "rig": RIG,
        "action": action.name,
        "armature_modifier": modifier.name,
        "preserve_volume": modifier.use_deform_preserve_volume,
        "limb_mode": "FK (IK_FK=0.0 on both arm and leg parents; verified from DEF matrices)",
        "constraint_repairs": constraint_repairs,
        "neutral_return_error_m": neutral_return_error,
        "poses": pose_metrics,
        "renders": rendered,
    }
    (AUDIT / "v277a_deformation_matrix.json").write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("V277A_DEFORMATION_MATRIX_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
