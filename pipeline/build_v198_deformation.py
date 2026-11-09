from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


STAGE_ROOT = Path(__file__).resolve().parents[1]
if str(STAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(STAGE_ROOT))

from pipeline.common import link_object_like, sha256, write_json


CONTACT_NAMES = [
    "V166_PICK",
    "V196_FRETTING_INDEX",
    "V196_FRETTING_MIDDLE",
    "V196_FRETTING_RING",
    "V196_FRETTING_PINKY",
    "V196_PICKING_THUMB",
    "V196_PICKING_INDEX",
]


def matrices_record(names: list[str]) -> dict[str, list[float]]:
    return {
        name: [round(float(value), 8) for row in bpy.data.objects[name].matrix_world for value in row]
        for name in names
    }


def record_hash(record: dict[str, list[float]]) -> str:
    return hashlib.sha256(json.dumps(record, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def reset_shapes() -> None:
    for obj in bpy.data.objects:
        shape_keys = getattr(obj.data, "shape_keys", None) if obj.data else None
        if shape_keys:
            for key in shape_keys.key_blocks:
                if key.name != "Basis":
                    key.value = 0.20 if key.name == "V198_CuffSeal" else 0.0


def reset_pose(rig: bpy.types.Object) -> None:
    action = bpy.data.actions.get("V197_PERFORMANCE_POSE")
    rig.animation_data_create()
    rig.animation_data.action = action
    bpy.context.scene.frame_set(1)
    for bone in rig.pose.bones:
        bone.rotation_mode = "XYZ"
        bone.location = (0.0, 0.0, 0.0)
        bone.rotation_euler = (0.0, 0.0, 0.0)
        bone.scale = (1.0, 1.0, 1.0)
    reset_shapes()
    bpy.context.view_layer.update()


def evaluated_center(name: str) -> Vector:
    depsgraph = bpy.context.evaluated_depsgraph_get()
    obj = bpy.data.objects[name].evaluated_get(depsgraph)
    return sum((obj.matrix_world @ Vector(corner) for corner in obj.bound_box), Vector()) / 8.0


def add_cuff_corrections() -> dict[str, object]:
    records = {}
    for suffix, hand_bone, palm_name in (
        ("L", "hand.L", "V196_FRETTING_HAND"),
        ("R", "hand.R", "V196_PICKING_HAND"),
    ):
        cuff = bpy.data.objects[f"V195_CUFF_{suffix}"]
        for group_name in (f"forearm.{suffix}", hand_bone):
            if cuff.vertex_groups.get(group_name) is None:
                cuff.vertex_groups.new(name=group_name)
        forearm = cuff.vertex_groups[f"forearm.{suffix}"]
        hand = cuff.vertex_groups[hand_bone]
        indices = [vertex.index for vertex in cuff.data.vertices]
        forearm.add(indices, 0.0, "REPLACE")
        hand.add(indices, 1.0, "REPLACE")
        if cuff.data.shape_keys is None:
            cuff.shape_key_add(name="Basis")
        key = cuff.data.shape_keys.key_blocks.get("V198_CuffSeal") or cuff.shape_key_add(name="V198_CuffSeal")
        cuff_center = evaluated_center(cuff.name)
        palm_center = evaluated_center(palm_name)
        direction_world = palm_center - cuff_center
        if direction_world.length:
            direction_world.normalize()
        direction_local = cuff.matrix_world.to_3x3().inverted() @ direction_world
        for point in key.data:
            point.co += direction_local * 0.0015
        key.value = 0.20
        records[cuff.name] = {
            "weights": {f"forearm.{suffix}": 0.0, hand_bone: 1.0},
            "shape_key": key.name,
            "seal_offset_m": 0.0015,
            "value": key.value,
        }
    return records


def activate(obj: bpy.types.Object) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def add_deformable_contact_surfaces(rig: bpy.types.Object) -> list[dict[str, str]]:
    records = []
    mapping = []
    for hand, side in (("FRETTING", "L"), ("PICKING", "R")):
        for digit in ("THUMB", "INDEX", "MIDDLE", "RING", "PINKY"):
            mapping.append((f"V196_{hand}_{digit}", f"V198_DEFORM_{hand}_{digit}", f"{digit.lower()}.{side}"))
    mapping.append(("V196_PICKING_WRIST_BRIDGE", "V198_DEFORM_PICKING_WRIST_BRIDGE", "hand.R"))
    for source_name, output_name, bone_name in mapping:
        source = bpy.data.objects[source_name]
        duplicate = source.copy()
        duplicate.data = source.data.copy()
        duplicate.name = output_name
        duplicate.hide_render = False
        duplicate.hide_viewport = False
        link_object_like(source, duplicate)
        activate(duplicate)
        bpy.ops.object.convert(target="MESH")
        duplicate.name = output_name
        for polygon in duplicate.data.polygons:
            polygon.use_smooth = True
        group = duplicate.vertex_groups.new(name=bone_name)
        group.add([vertex.index for vertex in duplicate.data.vertices], 1.0, "REPLACE")
        modifier = duplicate.modifiers.new("V198 Contact Deform", "ARMATURE")
        modifier.object = rig
        source.hide_render = True
        records.append({"analytic_source": source_name, "deform_surface": output_name, "bone": bone_name})
    return records


def point_segment_distance(point: Vector, start: Vector, end: Vector) -> tuple[float, float]:
    span = end - start
    if span.length_squared == 0.0:
        return (point - start).length, 0.0
    t = max(0.0, min(1.0, (point - start).dot(span) / span.length_squared))
    nearest = start + span * t
    return (point - nearest).length, t


def correct_arm_weights(rig: bpy.types.Object) -> dict[str, object]:
    deform_names = {bone.name for bone in rig.data.bones if bone.use_deform}
    geometry = {}
    for side in ("L", "R"):
        upper = rig.data.bones[f"upper_arm.{side}"]
        fore = rig.data.bones[f"forearm.{side}"]
        geometry[side] = {
            "shoulder": rig.matrix_world @ upper.head_local,
            "elbow": rig.matrix_world @ upper.tail_local,
            "wrist": rig.matrix_world @ fore.tail_local,
        }
    records = {}
    for object_name in ("V195_BODY", "V195_JACKET"):
        obj = bpy.data.objects[object_name]
        groups = {group.name: group for group in obj.vertex_groups}
        for side in ("L", "R"):
            for bone_name in (f"upper_arm.{side}", f"forearm.{side}", f"hand.{side}"):
                if bone_name not in groups:
                    groups[bone_name] = obj.vertex_groups.new(name=bone_name)
        changed = 0
        for vertex in obj.data.vertices:
            point = obj.matrix_world @ vertex.co
            candidates = []
            for side in ("L", "R"):
                upper_distance, upper_t = point_segment_distance(point, geometry[side]["shoulder"], geometry[side]["elbow"])
                fore_distance, fore_t = point_segment_distance(point, geometry[side]["elbow"], geometry[side]["wrist"])
                candidates.append((min(upper_distance, fore_distance), side, upper_distance, upper_t, fore_distance, fore_t))
            distance, side, upper_distance, upper_t, fore_distance, fore_t = min(candidates, key=lambda item: item[0])
            if distance > 0.105 or point.z < 1.08:
                continue
            for group in obj.vertex_groups:
                if group.name in deform_names:
                    group.add([vertex.index], 0.0, "REPLACE")
            elbow_distance = (point - geometry[side]["elbow"]).length
            wrist_distance = (point - geometry[side]["wrist"]).length
            if wrist_distance < 0.050:
                groups[f"forearm.{side}"].add([vertex.index], 0.25, "REPLACE")
                groups[f"hand.{side}"].add([vertex.index], 0.75, "REPLACE")
            elif elbow_distance < 0.065:
                groups[f"upper_arm.{side}"].add([vertex.index], 0.50, "REPLACE")
                groups[f"forearm.{side}"].add([vertex.index], 0.50, "REPLACE")
            elif upper_distance <= fore_distance:
                groups[f"upper_arm.{side}"].add([vertex.index], 1.0, "REPLACE")
            else:
                groups[f"forearm.{side}"].add([vertex.index], 1.0, "REPLACE")
            changed += 1
        records[object_name] = {"vertices_reweighted": changed, "method": "nearest arm segment with elbow/wrist blends"}
    return records


def strengthen_facial_tests() -> dict[str, object]:
    records = {}
    for suffix in ("L", "R"):
        for position, delta in (("UPPER", -0.0025), ("LOWER", 0.0018)):
            obj = bpy.data.objects[f"V194_{position}_LID_{suffix}"]
            keys = obj.data.shape_keys
            if keys and "Blink" in keys.key_blocks:
                key = keys.key_blocks["Blink"]
                for point in key.data:
                    point.co.z += delta
                records[obj.name] = {"Blink additional_z_m": delta}
    mouth = bpy.data.objects["V194_MOUTH"]
    if mouth.data.shape_keys and "Ah" in mouth.data.shape_keys.key_blocks:
        key = mouth.data.shape_keys.key_blocks["Ah"]
        for point in key.data:
            if point.co.z < -0.002:
                point.co.z -= 0.004
        records[mouth.name] = {"Ah lower_lip_additional_z_m": -0.004}
    return records


def weight_error_max(rig: bpy.types.Object) -> float:
    deform_names = {bone.name for bone in rig.data.bones if bone.use_deform}
    maximum = 0.0
    for obj in bpy.context.scene.objects:
        if obj.hide_render or obj.type != "MESH":
            continue
        if not any(modifier.type == "ARMATURE" and modifier.object == rig for modifier in obj.modifiers):
            continue
        group_names = {group.index: group.name for group in obj.vertex_groups}
        for vertex in obj.data.vertices:
            total = sum(element.weight for element in vertex.groups if group_names.get(element.group) in deform_names)
            maximum = max(maximum, abs(total - 1.0))
    return maximum


def set_shape(object_name: str, key_name: str, value: float) -> None:
    obj = bpy.data.objects.get(object_name)
    if obj and obj.data.shape_keys and key_name in obj.data.shape_keys.key_blocks:
        obj.data.shape_keys.key_blocks[key_name].value = value


def render_case(scene: bpy.types.Scene, output: Path, camera_name: str) -> None:
    camera = bpy.data.objects.get(camera_name)
    if camera is None or camera.type != "CAMERA":
        raise RuntimeError(f"Missing deformation camera: {camera_name}")
    scene.camera = camera
    scene.render.filepath = str(output)
    bpy.ops.render.render(write_still=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--stage-root", type=Path, default=STAGE_ROOT)
    return parser.parse_args(sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else [])


def main() -> None:
    args = parse_args()
    source = args.source.resolve()
    output = args.output.resolve()
    stage_root = args.stage_root.resolve()
    if Path(bpy.data.filepath).resolve() != source:
        raise RuntimeError(f"Loaded source mismatch: {bpy.data.filepath} != {source}")
    output.parent.mkdir(parents=True, exist_ok=True)
    rig = bpy.data.objects.get("V197_RIG")
    if rig is None:
        raise RuntimeError("Missing V197_RIG")
    contact_before = matrices_record(CONTACT_NAMES)
    reset_pose(rig)
    corrections = {
        "cuffs": add_cuff_corrections(),
        "contact_surfaces": add_deformable_contact_surfaces(rig),
        "arm_weights": correct_arm_weights(rig),
        "facial_tests": strengthen_facial_tests(),
    }
    normalization_error = weight_error_max(rig)
    if normalization_error > 1e-4:
        raise RuntimeError(f"Weight normalization error: {normalization_error}")

    production = stage_root / "production_v198_deformation"
    render_dir = production / "renders" / "matrix"
    render_dir.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 600
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    cases = [
        {"label": "shoulder_raise_35", "bone": "upper_arm.L", "rotation": (0.0, math.radians(35), 0.0), "camera": "V151_FRONT_CAMERA"},
        {"label": "elbow_bend_90", "bone": "forearm.L", "rotation": (math.radians(90), 0.0, 0.0), "camera": "V142_FRETTING_CAMERA"},
        {"label": "wrist_flex_pos25", "bone": "hand.L", "rotation": (math.radians(25), 0.0, 0.0), "camera": "V142_FRETTING_CAMERA"},
        {"label": "wrist_flex_neg25", "bone": "hand.R", "rotation": (math.radians(-25), 0.0, 0.0), "camera": "V166_PICKING_OBLIQUE_CAMERA"},
        {"label": "finger_curl", "bone": "index.L", "rotation": (math.radians(45), 0.0, 0.0), "camera": "V142_FRETTING_CAMERA"},
        {"label": "hip_flex_45", "bone": "thigh.L", "rotation": (math.radians(45), 0.0, 0.0), "camera": "V151_FRONT_CAMERA"},
        {"label": "knee_bend_90", "bone": "shin.L", "rotation": (math.radians(90), 0.0, 0.0), "camera": "V151_LEFT_PROFILE_CAMERA"},
        {"label": "neck_yaw_pos35", "bone": "head", "rotation": (0.0, math.radians(35), 0.0), "camera": "V95_CAM_HEAD_FRONT"},
        {"label": "neck_yaw_neg35", "bone": "head", "rotation": (0.0, math.radians(-35), 0.0), "camera": "V95_CAM_HEAD_FRONT"},
        {"label": "jaw_ah", "bone": "jaw", "rotation": (math.radians(16), 0.0, 0.0), "camera": "V95_CAM_HEAD_FRONT", "shape": ("V194_MOUTH", "Ah")},
        {"label": "blink", "bone": None, "rotation": None, "camera": "V95_CAM_HEAD_FRONT", "shape": ("V194_HEAD", "Blink")},
    ]
    baseline_cuff = {
        "L": (evaluated_center("V195_CUFF_L") - evaluated_center("V196_FRETTING_HAND")).length,
        "R": (evaluated_center("V195_CUFF_R") - evaluated_center("V196_PICKING_HAND")).length,
    }
    results = []
    max_cuff_delta = 0.0
    for case in cases:
        reset_pose(rig)
        rig.animation_data.action = None
        if case["bone"]:
            rig.pose.bones[case["bone"]].rotation_euler = case["rotation"]
        shape = case.get("shape")
        if shape:
            set_shape(shape[0], shape[1], 1.0)
            if shape[1] == "Blink":
                for suffix in ("L", "R"):
                    set_shape(f"V194_UPPER_LID_{suffix}", "Blink", 1.0)
                    set_shape(f"V194_LOWER_LID_{suffix}", "Blink", 1.0)
        bpy.context.view_layer.update()
        cuff_now = {
            "L": (evaluated_center("V195_CUFF_L") - evaluated_center("V196_FRETTING_HAND")).length,
            "R": (evaluated_center("V195_CUFF_R") - evaluated_center("V196_PICKING_HAND")).length,
        }
        cuff_delta = max(abs(cuff_now[side] - baseline_cuff[side]) for side in ("L", "R"))
        max_cuff_delta = max(max_cuff_delta, cuff_delta)
        render_path = render_dir / f"{case['label']}.png"
        render_case(scene, render_path, case["camera"])
        results.append(
            {
                "case": case["label"],
                "bone": case["bone"],
                "rotation_deg": [round(math.degrees(value), 3) for value in case["rotation"]] if case["rotation"] else None,
                "camera": case["camera"],
                "cuff_separation_delta_m": round(cuff_delta, 7),
                "render": str(render_path.relative_to(stage_root)),
                "render_sha256": sha256(render_path),
                "verdict": "PASS" if cuff_delta <= 0.006 else "FAIL",
            }
        )
    reset_pose(rig)
    contact_after = matrices_record(CONTACT_NAMES)
    restored_drift = 0.0
    for name in CONTACT_NAMES:
        before_translation = Vector((contact_before[name][3], contact_before[name][7], contact_before[name][11]))
        after_translation = Vector((contact_after[name][3], contact_after[name][7], contact_after[name][11]))
        restored_drift = max(restored_drift, (after_translation - before_translation).length)
    if contact_before != contact_after:
        raise RuntimeError("Performance contact matrices did not restore exactly")
    if max_cuff_delta > 0.006:
        raise RuntimeError(f"Cuff separation threshold failed: {max_cuff_delta:.7f}")

    scene["checkpoint"] = "V198"
    scene["checkpoint_intent"] = "deformation matrix with bounded cuff corrections and restored performance pose"
    scene["source_checkpoint"] = source.name
    scene["v198_matrix_verdict"] = "PASS"
    scene["v198_weight_error_max"] = normalization_error
    scene["v198_restored_contact_drift_m"] = restored_drift
    scene["v198_active_action"] = "V197_PERFORMANCE_POSE"
    scene["v198_max_cuff_separation_delta_m"] = max_cuff_delta
    bpy.ops.wm.save_as_mainfile(filepath=str(output), check_existing=False)

    audit_path = production / "audit" / "v198_deformation_audit.json"
    write_json(
        audit_path,
        {
            "schema": "v198-deformation-audit",
            "source": str(source),
            "output": str(output),
            "source_sha256": sha256(source),
            "output_sha256": sha256(output),
            "runtime": bpy.app.version_string,
            "thresholds": {
                "cuff_separation_m": 0.006,
                "weight_normalization_error": 1e-4,
                "restored_contact_drift_m": 0.0005,
            },
            "corrections": corrections,
            "matrix": results,
            "measurements": {
                "max_cuff_separation_delta_m": round(max_cuff_delta, 7),
                "weight_normalization_error_max": normalization_error,
                "restored_contact_drift_m": restored_drift,
                "contact_before": record_hash(contact_before),
                "contact_after": record_hash(contact_after),
            },
            "verdict": "PASS",
            "visual_review": "pending contact-sheet review",
        },
    )
    status = production / "HEADLESS_BUILD_STATUS_V198.md"
    status.parent.mkdir(parents=True, exist_ok=True)
    status.write_text(
        "# Character Asset_An — V198 Deformation\n\n"
        "V198 executes the prescribed shoulder, elbow, wrist, finger, hip, knee, neck, jaw, and blink matrix, applies bounded cuff sealing weights/keys, then restores the canonical performance pose.\n\n"
        f"- Max cuff separation delta: `{max_cuff_delta:.7f} m`\n"
        f"- Max normalized-weight error: `{normalization_error:.7g}`\n"
        f"- Restored contact drift: `{restored_drift:.7f} m`\n"
        "- Matrix verdict: PASS\n"
        "- Reopen validation: pending\n",
        encoding="utf-8",
    )
    print("V198_OUTPUT=" + str(output))


if __name__ == "__main__":
    main()
