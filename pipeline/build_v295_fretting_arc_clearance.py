"""Augment V250 fretting digits with base translation and solve neck clearance."""

from pathlib import Path
import hashlib
import json

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v294_pick_string_alignment" / "Character_An_pick_string_alignment_v294.blend"
STAGE = ROOT / "production_v295_fretting_arc_clearance"
OUTPUT = STAGE / "Character_An_fretting_arc_clearance_v295.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"
RIG = "V250_FRETTING_HAND_RIG"
NECK = "V206_NECK"
DIGITS = ("index", "middle", "ring", "pinky")


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            digest.update(block)
    return digest.hexdigest()


def point_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def bone_world(rig, point):
    return rig.matrix_world @ point


def neck_local(neck, point_world):
    return neck.matrix_world.inverted() @ point_world


def inside_penalty(local):
    # Expanded neck/fretboard envelope includes a skin-radius safety margin.
    x_min, x_max = -0.035, 0.610
    y_half = 0.055
    z_back, z_top = -0.035, 0.016
    if not (x_min < local.x < x_max and abs(local.y) < y_half and z_back < local.z < z_top):
        return 0.0
    distances = (
        local.x - x_min,
        x_max - local.x,
        y_half - abs(local.y),
        local.z - z_back,
        z_top - local.z,
    )
    clearance = min(distances)
    return (clearance + .004) ** 2


def samples_for_digit(rig, digit):
    result = []
    bones = [rig.pose.bones[f"{digit}_{joint:02d}"] for joint in range(1, 4)]
    for bone in bones:
        head = bone_world(rig, bone.head)
        tail = bone_world(rig, bone.tail)
        result.extend((head, head.lerp(tail, .33), head.lerp(tail, .66), tail))
    return result


def collision_metrics(rig, neck, digit):
    locals_ = [neck_local(neck, point) for point in samples_for_digit(rig, digit)]
    penalties = [inside_penalty(point) for point in locals_]
    return {
        "inside_samples": sum(value > 0.0 for value in penalties),
        "penalty": float(sum(penalties)),
        "samples_neck_local": [[round(float(v), 6) for v in point] for point in locals_],
    }


def solve_digit(rig, neck, digit):
    bones = [rig.pose.bones[f"{digit}_{joint:02d}"] for joint in range(1, 4)]
    for bone in bones:
        bone.rotation_mode = "XYZ"
    target_tail = bone_world(rig, bones[-1].tail).copy()
    base_location = bones[0].location.copy()
    variables = [
        (bones[0], "location", axis, base_location[axis] - .040, base_location[axis] + .040, .018)
        for axis in range(3)
    ] + [
        (bones[0], "rotation_euler", 0, -.45, .82, .28),
        (bones[0], "rotation_euler", 1, -.78, .78, .28),
        (bones[0], "rotation_euler", 2, -.78, .78, .28),
        (bones[1], "rotation_euler", 0, -.10, 1.25, .28),
        (bones[2], "rotation_euler", 0, -.10, 1.00, .28),
    ]

    def objective():
        tail = bone_world(rig, bones[-1].tail)
        contact = (tail - target_tail).length_squared * 18.0
        collision = collision_metrics(rig, neck, digit)["penalty"] * 10.0
        translation = (bones[0].location - base_location).length_squared * .025
        return contact + collision + translation

    before = collision_metrics(rig, neck, digit)
    best = objective()
    evaluations = 1
    for scale in (1.0, .52, .27, .14, .07, .035):
        for _ in range(5):
            improved = False
            for bone, path, axis, lower, upper, initial_step in variables:
                vector = getattr(bone, path)
                base = float(vector[axis])
                local_value, local_best = base, best
                step = initial_step * scale
                for candidate in (max(lower, base - step), min(upper, base + step)):
                    vector[axis] = candidate
                    bpy.context.view_layer.update()
                    value = objective()
                    evaluations += 1
                    if value < local_best:
                        local_best = value
                        local_value = candidate
                vector[axis] = local_value
                bpy.context.view_layer.update()
                if local_best + 1e-14 < best:
                    best = local_best
                    improved = True
            if not improved:
                break
    after = collision_metrics(rig, neck, digit)
    final_tail = bone_world(rig, bones[-1].tail)
    return {
        "evaluations": evaluations,
        "target_tail_world": [float(v) for v in target_tail],
        "final_tail_world": [float(v) for v in final_tail],
        "tail_error_m": float((final_tail - target_tail).length),
        "base_translation": [float(v) for v in bones[0].location],
        "before": before,
        "after": after,
        "rotations_xyz_rad": {bone.name: [float(v) for v in bone.rotation_euler] for bone in bones},
    }


def render(scene, camera, path, resolution):
    scene.camera = camera
    scene.render.resolution_x, scene.render.resolution_y = resolution
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(path)}


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    for folder in (STAGE, RENDERS, AUDIT):
        folder.mkdir(parents=True, exist_ok=True)
    rig = bpy.data.objects[RIG]
    neck = bpy.data.objects[NECK]
    solves = {}
    for digit in DIGITS:
        solves[digit] = solve_digit(rig, neck, digit)
    bpy.context.view_layer.update()

    scene = bpy.context.scene
    camera = bpy.data.objects["V287_GUITAR_CAMERA"]
    center = neck.matrix_world @ Vector((.33, 0.0, -.005))
    player_side = center + neck.matrix_world.to_3x3() @ Vector((0.0, .55, -.48))
    views = {
        "full": (Vector((0.0, -3.75, 1.02)), Vector((0.0, -0.02, 1.0)), 66.0, (900, 1000)),
        "contact_front": (Vector((0.72, -1.48, 1.49)), Vector((0.27, -0.39, 1.39)), 105.0, (1200, 900)),
        "player_side": (player_side, center, 105.0, (1200, 900)),
    }
    renders = {}
    for label, (location, target, lens, resolution) in views.items():
        camera.location = location
        camera.data.lens = lens
        point_at(camera, target)
        renders[label] = render(scene, camera, RENDERS / f"v295_{label}.png", resolution)
    scene["V295_STATUS"] = "FRETTING_ARC_CLEARANCE_VISUAL_REVIEW_REQUIRED"
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v295-fretting-arc-clearance-v1",
        "status": "VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)},
        "solves": solves,
        "renders": renders,
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha(OUTPUT)},
    }
    (AUDIT / "v295_fretting_arc_clearance.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V295_FRETTING_ARC_CLEARANCE_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
