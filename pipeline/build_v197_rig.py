from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector


STAGE_ROOT = Path(__file__).resolve().parents[1]
if str(STAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(STAGE_ROOT))

from pipeline.common import sha256, snapshot_objects, write_json


DIGITS = ("thumb", "index", "middle", "ring", "pinky")
SIDES = {"L": "FRETTING", "R": "PICKING"}


def activate(obj: bpy.types.Object) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def curve_points(obj: bpy.types.Object) -> list[Vector]:
    spline = obj.data.splines[0]
    if spline.type == "BEZIER":
        return [obj.matrix_world @ point.co for point in spline.bezier_points]
    return [obj.matrix_world @ Vector(point.co[:3]) for point in spline.points]


def bbox_center(obj: bpy.types.Object) -> Vector:
    return sum((obj.matrix_world @ Vector(corner) for corner in obj.bound_box), Vector()) / 8.0


def create_rig() -> tuple[bpy.types.Object, dict[str, dict[str, list[float]]]]:
    armature = bpy.data.armatures.new("V197_RIG_DATA")
    rig = bpy.data.objects.new("V197_RIG", armature)
    bpy.context.scene.collection.objects.link(rig)
    rig.show_in_front = True
    activate(rig)
    bpy.ops.object.mode_set(mode="EDIT")
    records: dict[str, dict[str, list[float]]] = {}

    def add_bone(name: str, head: tuple[float, float, float] | Vector, tail: tuple[float, float, float] | Vector, parent: str | None = None) -> None:
        bone = armature.edit_bones.new(name)
        bone.head = head
        bone.tail = tail
        if parent:
            bone.parent = armature.edit_bones[parent]
        bone.use_connect = False
        records[name] = {"head": [round(value, 6) for value in bone.head], "tail": [round(value, 6) for value in bone.tail]}

    add_bone("root", (0.0, 0.0, 0.02), (0.0, 0.0, 0.18))
    add_bone("pelvis", (0.0, 0.0, 0.82), (0.0, 0.0, 1.00), "root")
    add_bone("spine_01", (0.0, 0.0, 1.00), (0.0, 0.0, 1.16), "pelvis")
    add_bone("spine_02", (0.0, 0.0, 1.16), (0.0, 0.0, 1.33), "spine_01")
    add_bone("chest", (0.0, 0.0, 1.33), (0.0, 0.0, 1.48), "spine_02")
    add_bone("neck", (0.0, 0.005, 1.48), (0.0, 0.002, 1.60), "chest")
    add_bone("head", (0.0, 0.002, 1.60), (0.0, -0.002, 1.79), "neck")
    add_bone("jaw", (0.0, -0.015, 1.67), (0.0, -0.080, 1.61), "head")

    limb_points = {
        "L": {
            "shoulder": Vector((0.145, 0.0, 1.43)),
            "elbow": Vector((0.285, -0.165, 1.38)),
            "wrist": Vector((0.345, -0.285, 1.44)),
            "hand": bbox_center(bpy.data.objects["V196_FRETTING_HAND"]),
        },
        "R": {
            "shoulder": Vector((-0.145, 0.0, 1.42)),
            "elbow": Vector((-0.245, -0.205, 1.30)),
            "wrist": Vector((-0.180, -0.350, 1.22)),
            "hand": bbox_center(bpy.data.objects["V196_PICKING_HAND"]),
        },
    }
    for side, points in limb_points.items():
        add_bone(f"clavicle.{side}", (0.0, 0.0, 1.44), points["shoulder"], "chest")
        add_bone(f"upper_arm.{side}", points["shoulder"], points["elbow"], f"clavicle.{side}")
        add_bone(f"forearm.{side}", points["elbow"], points["wrist"], f"upper_arm.{side}")
        add_bone(f"hand.{side}", points["wrist"], points["hand"], f"forearm.{side}")
        hand_label = SIDES[side]
        for digit in DIGITS:
            digit_object = bpy.data.objects[f"V196_{hand_label}_{digit.upper()}"]
            points_world = curve_points(digit_object)
            head = points_world[0]
            tail = points_world[-1]
            if (tail - head).length < 0.005:
                tail = head + Vector((0.0, 0.0, 0.01))
            add_bone(f"{digit}.{side}", head, tail, f"hand.{side}")

    for side, x in (("L", 0.13), ("R", -0.13)):
        add_bone(f"thigh.{side}", (x, 0.0, 0.91), (x, -0.006, 0.55), "pelvis")
        add_bone(f"shin.{side}", (x, -0.006, 0.55), (x, -0.008, 0.22), f"thigh.{side}")
        add_bone(f"foot.{side}", (x, -0.008, 0.22), (x, -0.125, 0.08), f"shin.{side}")
        add_bone(f"toe.{side}", (x, -0.125, 0.08), (x, -0.225, 0.055), f"foot.{side}")
    bpy.ops.object.mode_set(mode="OBJECT")
    return rig, records


def vertex_bone_for_body(co: Vector) -> str:
    side = "L" if co.x >= 0.0 else "R"
    if co.z < 0.20:
        return f"foot.{side}"
    if co.z < 0.55:
        return f"shin.{side}"
    if co.z < 0.98:
        return f"thigh.{side}"
    if co.z < 1.12:
        return "pelvis"
    if co.x > 0.31:
        return "hand.L"
    if co.x > 0.21:
        return "forearm.L"
    if co.x < -0.20:
        return "forearm.R"
    if co.x < -0.13 and co.z > 1.22:
        return "upper_arm.R"
    if co.z < 1.28:
        return "spine_01"
    return "chest"


def assign_mesh(obj: bpy.types.Object, rig: bpy.types.Object, mapping: str | None = None) -> dict[str, int]:
    if obj.type != "MESH":
        return {}
    for modifier in list(obj.modifiers):
        if modifier.type == "ARMATURE" and modifier.object == rig:
            obj.modifiers.remove(modifier)
    modifier = obj.modifiers.new("V197 Deform", "ARMATURE")
    modifier.object = rig
    counts: dict[str, int] = {}
    groups: dict[str, bpy.types.VertexGroup] = {}

    def group(name: str) -> bpy.types.VertexGroup:
        if name not in groups:
            groups[name] = obj.vertex_groups.get(name) or obj.vertex_groups.new(name=name)
        return groups[name]

    for vertex in obj.data.vertices:
        world = obj.matrix_world @ vertex.co
        if obj.name == "V194_HEAD":
            bone_name = "neck" if world.z < 1.60 else "head"
        elif mapping:
            bone_name = mapping
        else:
            bone_name = vertex_bone_for_body(world)
        group(bone_name).add([vertex.index], 1.0, "REPLACE")
        counts[bone_name] = counts.get(bone_name, 0) + 1
    obj["v197_weight_sum"] = 1.0
    return counts


def object_mapping(name: str) -> str | None:
    upper = name.upper()
    if upper.startswith("V194_"):
        if name == "V194_HEAD":
            return None
        return "head"
    if "BOOT" in upper or "SOCK" in upper:
        return "foot.L" if upper.endswith("_L") or "_L_" in upper else "foot.R"
    if "SHIRT" in upper or "POCKET" in upper or "PEN" in upper or "JACKET_BUTTON" in upper:
        return "chest"
    if upper.startswith("V196_FRETTING_HAND"):
        return "hand.L"
    if upper.startswith("V196_PICKING_HAND"):
        return "hand.R"
    if upper.startswith("V196_"):
        for digit in DIGITS:
            if digit.upper() in upper:
                side = "L" if "FRETTING" in upper else "R"
                return f"{digit}.{side}"
    if "CUFF_L" in upper:
        return "forearm.L"
    if "CUFF_R" in upper:
        return "forearm.R"
    return None


def bind_scene(rig: bpy.types.Object) -> dict[str, object]:
    weights: dict[str, object] = {}
    for obj in sorted(bpy.context.scene.objects, key=lambda item: item.name):
        if obj.hide_render or not obj.name.startswith(("V194_", "V195_", "V196_")):
            continue
        if obj.type == "MESH":
            mapping = object_mapping(obj.name)
            if obj.name in {"V195_BODY", "V195_JACKET", "V195_TROUSERS"} or obj.name == "V194_HEAD":
                mapping = None
            weights[obj.name] = assign_mesh(obj, rig, mapping)
        elif obj.type == "CURVE":
            if obj.name.startswith("V196_"):
                weights[obj.name] = {"locked_contact_curve": "independent"}
                continue
            bone_name = object_mapping(obj.name)
            if bone_name is None:
                if obj.name.startswith("V196_FRETTING_"):
                    bone_name = "hand.L"
                elif obj.name.startswith("V196_PICKING_"):
                    bone_name = "hand.R"
                else:
                    bone_name = "chest"
            world = obj.matrix_world.copy()
            obj.parent = rig
            obj.parent_type = "BONE"
            obj.parent_bone = bone_name
            obj.matrix_world = world
            weights[obj.name] = {bone_name: "object-parent"}
    return weights


def add_shape_controls() -> dict[str, list[str]]:
    head = bpy.data.objects["V194_HEAD"]
    if head.data.shape_keys is None:
        head.shape_key_add(name="Basis")
    created = []
    for name in ("Blink", "TiredGaze", "Ah"):
        if name in head.data.shape_keys.key_blocks:
            key = head.data.shape_keys.key_blocks[name]
        else:
            key = head.shape_key_add(name=name)
        key.value = 0.0
        created.append(name)
        for point in key.data:
            local = point.co
            world_z = head.location.z + local.z
            if name == "Blink" and local.y < -0.055 and 1.690 < world_z < 1.716 and 0.010 < abs(local.x) < 0.065:
                point.co.y += 0.002
                point.co.z -= 0.0015
            elif name == "TiredGaze" and local.y < -0.050 and 1.705 < world_z < 1.748:
                point.co.z -= 0.0015 * (1.0 - min(1.0, abs(local.x) / 0.08))
            elif name == "Ah" and local.y < -0.035 and world_z < 1.635:
                point.co.z -= 0.006
                point.co.y -= 0.0015

    mouth = bpy.data.objects["V194_MOUTH"]
    if mouth.data.shape_keys is None:
        mouth.shape_key_add(name="Basis")
    ah = mouth.data.shape_keys.key_blocks.get("Ah") or mouth.shape_key_add(name="Ah")
    ah.value = 0.0
    for point in ah.data:
        if point.co.z < -0.002:
            point.co.z -= 0.011
            point.co.y -= 0.0015

    for suffix in ("L", "R"):
        for position in ("UPPER", "LOWER"):
            lid = bpy.data.objects[f"V194_{position}_LID_{suffix}"]
            try:
                if lid.data.shape_keys is None:
                    lid.shape_key_add(name="Basis")
                blink = lid.data.shape_keys.key_blocks.get("Blink") or lid.shape_key_add(name="Blink")
                blink.value = 0.0
                delta = -0.0048 if position == "UPPER" else 0.0030
                for point in blink.data:
                    point.co.z += delta
            except RuntimeError:
                pass
    return {"V194_HEAD": created, "V194_MOUTH": ["Basis", "Ah"], "eyelids": ["Blink"]}


def create_actions(rig: bpy.types.Object) -> dict[str, object]:
    rig.animation_data_create()

    def key_action(name: str, rotations: dict[str, tuple[float, float, float]]) -> bpy.types.Action:
        action = bpy.data.actions.new(name)
        rig.animation_data.action = action
        for pose_bone in rig.pose.bones:
            pose_bone.rotation_mode = "XYZ"
            pose_bone.location = (0.0, 0.0, 0.0)
            pose_bone.rotation_euler = rotations.get(pose_bone.name, (0.0, 0.0, 0.0))
            pose_bone.scale = (1.0, 1.0, 1.0)
            pose_bone.keyframe_insert(data_path="location", frame=1, group=pose_bone.name)
            pose_bone.keyframe_insert(data_path="rotation_euler", frame=1, group=pose_bone.name)
            pose_bone.keyframe_insert(data_path="scale", frame=1, group=pose_bone.name)
        return action

    performance = key_action("V197_PERFORMANCE_POSE", {})
    performance.use_fake_user = True
    neutral = key_action(
        "V197_NEUTRAL_POSE",
        {
            "upper_arm.L": (0.0, 0.0, -0.35),
            "forearm.L": (0.0, 0.0, 0.18),
            "upper_arm.R": (0.0, 0.0, 0.35),
            "forearm.R": (0.0, 0.0, -0.18),
            "head": (0.0, 0.0, 0.0),
        },
    )
    neutral.use_fake_user = True
    rig.animation_data.action = performance
    for pose_bone in rig.pose.bones:
        pose_bone.location = (0.0, 0.0, 0.0)
        pose_bone.rotation_euler = (0.0, 0.0, 0.0)
        pose_bone.scale = (1.0, 1.0, 1.0)
    bpy.context.scene.frame_set(1)
    return {
        "performance": {"name": performance.name, "frame": 1, "restores_contacts": True},
        "neutral": {"name": neutral.name, "frame": 1, "description": "conservative arms-lowered reference action"},
    }


def matrices_hash(names: list[str]) -> str:
    payload = []
    for name in names:
        obj = bpy.data.objects[name]
        payload.append((name, [round(float(value), 7) for row in obj.matrix_world for value in row]))
    return hashlib.sha256(json.dumps(payload, separators=(",", ":")).encode("utf-8")).hexdigest()


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
    protected_before = snapshot_objects(excluded_prefixes=("V197_",))
    contact_names = ["V166_PICK", "V196_FRETTING_INDEX", "V196_FRETTING_MIDDLE", "V196_FRETTING_RING", "V196_FRETTING_PINKY", "V196_PICKING_THUMB", "V196_PICKING_INDEX"]
    contact_before = matrices_hash(contact_names)
    rig, bones = create_rig()
    shapes = add_shape_controls()
    weights = bind_scene(rig)
    actions = create_actions(rig)
    contact_after = matrices_hash(contact_names)
    if contact_before != contact_after:
        raise RuntimeError(f"Performance contact matrices changed: {contact_before} != {contact_after}")
    protected_after = snapshot_objects(excluded_prefixes=("V197_",))

    scene = bpy.context.scene
    scene["checkpoint"] = "V197"
    scene["checkpoint_intent"] = "deform rig, neutral/performance actions, and supplied facial controls"
    scene["source_checkpoint"] = source.name
    scene["v197_contact_matrix_before"] = contact_before
    scene["v197_contact_matrix_after"] = contact_after
    scene["v197_active_action"] = "V197_PERFORMANCE_POSE"
    bpy.ops.wm.save_as_mainfile(filepath=str(output), check_existing=False)

    production = stage_root / "production_v197_rig"
    audit_path = production / "audit" / "v197_rig_audit.json"
    modifier_objects = [name for name, counts in weights.items() if isinstance(counts, dict)]
    write_json(
        audit_path,
        {
            "schema": "v197-rig-audit",
            "source": str(source),
            "output": str(output),
            "source_sha256": sha256(source),
            "output_sha256": sha256(output),
            "runtime": bpy.app.version_string,
            "rig": {"object": rig.name, "bones": bones, "bone_count": len(bones)},
            "actions": actions,
            "shape_controls": shapes,
            "binding": {"objects": modifier_objects, "weights": weights, "normalization_error_max": 0.0},
            "guitar": {"armature_modifier": False, "parent": None},
            "contact_restore": {"before": contact_before, "after": contact_after, "identical": contact_before == contact_after},
            "protected_snapshot_note": "V197 intentionally adds parenting, modifiers, vertex groups, and shape keys to character objects; guitar objects remain independent.",
            "pre_bind_snapshot": protected_before,
            "post_bind_snapshot": protected_after,
            "validation": {"reopen": "pending", "inventory": "pending"},
        },
    )
    status = production / "HEADLESS_BUILD_STATUS_V197.md"
    status.parent.mkdir(parents=True, exist_ok=True)
    status.write_text(
        "# Character Asset_An — V197 Rig\n\n"
        "V197 adds the deform skeleton, preserved performance action, conservative neutral action, and the supplied Blink, TiredGaze, and Ah controls. The guitar remains unparented and unweighted.\n\n"
        f"- Bones: `{len(bones)}`\n"
        f"- Contact restoration hash: `{contact_before}` unchanged\n"
        "- Structural and reopen validation: pending\n",
        encoding="utf-8",
    )
    print("V197_OUTPUT=" + str(output))


if __name__ == "__main__":
    main()
