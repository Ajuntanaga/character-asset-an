"""Rebind V248's realistic hand to one anatomical digit chain per surface region."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v248_topology_hand_replacement" / "Character_An_topology_hand_v248.blend"
STAGE = ROOT / "production_v249_hand_bind_repair"
OUTPUT = STAGE / "Character_An_hand_bind_v249.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"
RIG_NAME = "V239_CLEAN_CHARACTER_RIG"
HAND_NAME = "V248_FRETTING_HAND_REALISTIC"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def point_at(obj: bpy.types.Object, target: Vector) -> None:
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def segment_distance(point: Vector, start: Vector, end: Vector) -> float:
    vector = end - start
    length = vector.length_squared
    if length <= 1e-12:
        return (point - start).length
    factor = max(0.0, min(1.0, (point - start).dot(vector) / length))
    return (point - (start + factor * vector)).length


def main() -> None:
    if Path(bpy.data.filepath).resolve() != SOURCE.resolve():
        raise RuntimeError(f"Open V248 first: {SOURCE}")
    STAGE.mkdir(parents=True, exist_ok=True)
    RENDERS.mkdir(parents=True, exist_ok=True)
    AUDIT.mkdir(parents=True, exist_ok=True)
    rig = bpy.data.objects[RIG_NAME]
    hand = bpy.data.objects[HAND_NAME]
    rig.data.pose_position = "REST"
    bpy.context.view_layer.update()

    chain_names = {
        digit: [f"DEF-f_{digit}.0{joint}.L" for joint in range(1, 4)]
        for digit in ("index", "middle", "ring", "pinky")
    }
    chain_names["thumb"] = [f"DEF-thumb.0{joint}.L" for joint in range(1, 4)]
    segments = {
        digit: [
            (
                rig.matrix_world @ rig.data.bones[name].head_local,
                rig.matrix_world @ rig.data.bones[name].tail_local,
            )
            for name in names
        ]
        for digit, names in chain_names.items()
    }
    hand_group_name = "DEF-hand.L"
    all_groups = {name for names in chain_names.values() for name in names} | {hand_group_name}
    groups = {name: hand.vertex_groups.get(name) or hand.vertex_groups.new(name=name) for name in all_groups}
    indices = [vertex.index for vertex in hand.data.vertices]
    for group in hand.vertex_groups:
        if group.name.startswith("DEF-"):
            group.remove(indices)

    assignments = {digit: 0 for digit in chain_names}
    assignments["hand"] = 0
    for vertex in hand.data.vertices:
        point = hand.matrix_world @ vertex.co
        distances = {
            digit: min(segment_distance(point, *segment) for segment in digit_segments)
            for digit, digit_segments in segments.items()
        }
        digit = min(distances, key=distances.get)
        # Keep wrist/palm rigid and allow only the distal hand surface to enter
        # one digit chain. This prevents neighboring fingers sharing weights.
        if point.z > 1.005 or distances[digit] > 0.046:
            groups[hand_group_name].add([vertex.index], 1.0, "REPLACE")
            assignments["hand"] += 1
            continue
        local = [segment_distance(point, *segment) for segment in segments[digit]]
        ranked = sorted(range(3), key=lambda index: local[index])[:2]
        raw = [(index, 1.0 / ((local[index] + 0.0025) ** 4.0)) for index in ranked]
        total = sum(value for _, value in raw)
        for index, value in raw:
            groups[chain_names[digit][index]].add([vertex.index], value / total, "REPLACE")
        assignments[digit] += 1

    rig.data.pose_position = "POSE"
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.look = "AgX - Medium High Contrast"
    camera = bpy.data.objects["CAM_V211_FRONT"]
    camera.data.type = "PERSP"

    def render(label: str, location: Vector, target: Vector, lens: float, resolution=(1200, 900)) -> Path:
        camera.location = location
        camera.data.lens = lens
        point_at(camera, target)
        scene.camera = camera
        scene.render.resolution_x, scene.render.resolution_y = resolution
        scene.render.resolution_percentage = 100
        path = RENDERS / f"v249_{label}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        return path

    neutral = render("neutral_hand", Vector((0.72, -1.48, 1.49)), Vector((0.27, -0.39, 1.39)), 105.0)
    controls = []
    for digit in ("index", "middle", "ring", "pinky"):
        first = rig.pose.bones[f"f_{digit}.01.L"]
        second = rig.pose.bones[f"f_{digit}.02.L"]
        third = rig.pose.bones[f"f_{digit}.03.L"]
        for control in (first, second, third):
            control.rotation_mode = "XYZ"
        first.rotation_euler.x = 0.22
        second.rotation_euler.x = 0.82
        third.rotation_euler.x = 0.56
        controls.extend((first, second, third))
    for joint, angle in zip(("01", "02", "03"), (0.18, 0.55, 0.42)):
        control = rig.pose.bones[f"thumb.{joint}.L"]
        control.rotation_mode = "XYZ"
        control.rotation_euler.x = angle
        controls.append(control)
    bpy.context.view_layer.update()
    flexed = render("flex_test", Vector((0.72, -1.48, 1.49)), Vector((0.27, -0.39, 1.39)), 105.0)
    for control in controls:
        control.rotation_euler = (0.0, 0.0, 0.0)
    bpy.context.view_layer.update()

    scene["V249_STATUS"] = "REALISTIC_HAND_EXCLUSIVE_DIGIT_BIND_VISUAL_REVIEW_REQUIRED"
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v249-hand-bind-repair-v1",
        "status": "BUILT_VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha256(SOURCE)},
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha256(OUTPUT)},
        "hand": HAND_NAME,
        "assignments": assignments,
        "exclusive_digit_chains": True,
        "renders": {
            "neutral": {"path": str(neutral.relative_to(ROOT)), "sha256": sha256(neutral)},
            "flex_test": {"path": str(flexed.relative_to(ROOT)), "sha256": sha256(flexed)},
        },
    }
    (AUDIT / "v249_hand_bind.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("V249_HAND_BIND_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
