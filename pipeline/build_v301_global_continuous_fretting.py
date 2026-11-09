"""Solve the continuous dedicated hand using hub pose plus joint rotations only."""

from pathlib import Path
import hashlib
import json
import math

import bpy
from mathutils import Euler, Matrix, Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v300_guitar_visual_acceptance" / "Character_An_guitar_visual_acceptance_v300.blend"
STAGE = ROOT / "production_v301_global_continuous_fretting"
OUTPUT = STAGE / "Character_An_global_continuous_fretting_v301.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"
RIG = "V250_FRETTING_HAND_RIG"
HAND = "V248_FRETTING_HAND_REALISTIC"
HUB = "V250_FRETTING_HAND_HUB"
NECK = "V206_NECK"
CONTACTS = {
    "index": (234, 0.3058091, 0.0041983, "S5", 9),
    "middle": (211, 0.3296208, -0.0042574, "S4", 10),
    "ring": (14, 0.3050833, 0.0209915, "S7", 9),
    "pinky": (225, 0.3488616, 0.0301914, "S8", 11),
}
THUMB = (286, Vector((0.3425739, 0.0034927, -0.0270)))


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            digest.update(block)
    return digest.hexdigest()


def point_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def string_z_at_x(obj, x):
    points = [Vector(point.co[:3]) for spline in obj.data.splines for point in spline.points]
    for a, b in zip(points, points[1:]):
        if min(a.x, b.x) <= x <= max(a.x, b.x):
            factor = (x - a.x) / (b.x - a.x)
            return a.z + factor * (b.z - a.z)
    return min(points, key=lambda point: abs(point.x - x)).z


def target_world(neck, spec):
    _vertex, x, y, string_id, _fret = spec
    string = bpy.data.objects[f"V206_STRING_{string_id}"]
    z = string_z_at_x(string, x) - .00185 + float(string.data.bevel_depth)
    return neck.matrix_world @ Vector((x, y, z))


def surface_points(hand, vertex_indices):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = hand.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    try:
        return {index: evaluated.matrix_world @ mesh.vertices[index].co for index in vertex_indices}
    finally:
        evaluated.to_mesh_clear()


def penetration(neck, point):
    local = neck.matrix_world.inverted() @ point
    if not (-.035 < local.x < .610 and abs(local.y) < .054 and -.038 < local.z < .018):
        return 0.0
    return min(local.x + .035, .610 - local.x, .054 - abs(local.y), local.z + .038, .018 - local.z) + .0025


def arc_penalty(rig, neck, digit):
    total = 0.0
    inside = 0
    samples = []
    joints = (1, 2) if digit != "thumb" else (1, 2)
    for joint in joints:
        bone = rig.pose.bones[f"{digit}_{joint:02d}"]
        head = rig.matrix_world @ bone.head
        tail = rig.matrix_world @ bone.tail
        for point in (head, head.lerp(tail, .33), head.lerp(tail, .66), tail):
            depth = penetration(neck, point)
            total += depth * depth
            inside += int(depth > 0.0)
            samples.append(neck.matrix_world.inverted() @ point)
    distal = rig.pose.bones[f"{digit}_03"]
    head = rig.matrix_world @ distal.head
    tail = rig.matrix_world @ distal.tail
    for point in (head, head.lerp(tail, .30)):
        depth = penetration(neck, point)
        total += depth * depth
        inside += int(depth > 0.0)
        samples.append(neck.matrix_world.inverted() @ point)
    return total, inside, samples


def hub_matrix(base, translation, rotation):
    pivot = base.translation
    rotate = Euler(rotation, "XYZ").to_matrix().to_4x4()
    return Matrix.Translation(translation) @ Matrix.Translation(pivot) @ rotate @ Matrix.Translation(-pivot) @ base


def solve(rig, hand, hub, neck, targets):
    base_hub = hub.matrix_world.copy()
    hub_translation = Vector((0.0, 0.0, 0.0))
    hub_rotation = Vector((0.0, 0.0, 0.0))
    for digit in (*CONTACTS.keys(), "thumb"):
        for joint in range(1, 4):
            bone = rig.pose.bones[f"{digit}_{joint:02d}"]
            bone.rotation_mode = "XYZ"
            bone.location = (0.0, 0.0, 0.0)
    bpy.context.view_layer.update()

    variables = []
    for axis in range(3):
        variables.append(("hub_t", hub_translation, axis, -.065, .065, .020))
    for axis in range(3):
        variables.append(("hub_r", hub_rotation, axis, math.radians(-38), math.radians(38), math.radians(13)))
    for digit in (*CONTACTS.keys(), "thumb"):
        bones = [rig.pose.bones[f"{digit}_{joint:02d}"] for joint in range(1, 4)]
        variables.extend([
            ("bone", bones[0].rotation_euler, 0, -.65 if digit != "thumb" else -.80, 1.05, .22),
            ("bone", bones[0].rotation_euler, 1, -.90, .90, .20),
            ("bone", bones[0].rotation_euler, 2, -.90, .90, .20),
            ("bone", bones[1].rotation_euler, 0, -.18, 1.40 if digit != "thumb" else 1.15, .22),
            ("bone", bones[2].rotation_euler, 0, -.18, 1.15 if digit != "thumb" else .95, .20),
        ])
    vertex_indices = [value[0] for value in CONTACTS.values()] + [THUMB[0]]

    def update_hub():
        hub.matrix_world = hub_matrix(base_hub, hub_translation, hub_rotation)
        bpy.context.view_layer.update()

    def objective(detail=False):
        points = surface_points(hand, vertex_indices)
        contact_sq = 0.0
        errors = {}
        for digit, (vertex, _x, _y, _string, _fret) in CONTACTS.items():
            error = (points[vertex] - targets[digit]).length
            errors[digit] = error
            contact_sq += error * error
        thumb_error = (points[THUMB[0]] - targets["thumb"]).length
        errors["thumb"] = thumb_error
        contact_sq += thumb_error * thumb_error * .55
        collision = 0.0
        inside = {}
        for digit in (*CONTACTS.keys(), "thumb"):
            penalty, count, _samples = arc_penalty(rig, neck, digit)
            collision += penalty
            inside[digit] = count
        regularizer = hub_translation.length_squared * .08 + hub_rotation.length_squared * .0008
        value = contact_sq * 2800.0 + collision * 260.0 + regularizer
        if detail:
            return value, errors, inside, points
        return value

    update_hub()
    best = objective()
    evaluations = 1
    for scale in (1.0, .52, .27, .14, .07, .035):
        for _pass in range(3):
            improved = False
            for kind, vector, axis, lower, upper, initial_step in variables:
                base = float(vector[axis])
                local_value = base
                local_best = best
                step = initial_step * scale
                for candidate in (max(lower, base - step), min(upper, base + step)):
                    vector[axis] = candidate
                    if kind.startswith("hub"):
                        update_hub()
                    else:
                        bpy.context.view_layer.update()
                    value = objective()
                    evaluations += 1
                    if value < local_best:
                        local_best = value
                        local_value = candidate
                vector[axis] = local_value
                if kind.startswith("hub"):
                    update_hub()
                else:
                    bpy.context.view_layer.update()
                if local_best + 1e-12 < best:
                    best = local_best
                    improved = True
            if not improved:
                break
    value, errors, inside, points = objective(detail=True)
    return {
        "evaluations": evaluations,
        "objective": float(value),
        "hub_translation_m": [float(v) for v in hub_translation],
        "hub_rotation_rad": [float(v) for v in hub_rotation],
        "surface_errors_m": {name: float(error) for name, error in errors.items()},
        "inside_samples": inside,
        "surface_world": {digit: [float(v) for v in points[spec[0]]] for digit, spec in CONTACTS.items()},
        "thumb_surface_world": [float(v) for v in points[THUMB[0]]],
        "rotations": {
            f"{digit}_{joint:02d}": [float(v) for v in rig.pose.bones[f"{digit}_{joint:02d}"].rotation_euler]
            for digit in (*CONTACTS.keys(), "thumb") for joint in range(1, 4)
        },
    }


def render(scene, camera, path, location, target, lens, resolution):
    camera.location = location
    camera.data.lens = lens
    point_at(camera, target)
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
    hand = bpy.data.objects[HAND]
    hub = bpy.data.objects[HUB]
    neck = bpy.data.objects[NECK]
    targets = {digit: target_world(neck, spec) for digit, spec in CONTACTS.items()}
    targets["thumb"] = neck.matrix_world @ THUMB[1]
    result = solve(rig, hand, hub, neck, targets)
    bpy.context.view_layer.update()

    scene = bpy.context.scene
    camera = bpy.data.objects["V287_GUITAR_CAMERA"]
    focus = Vector((.262, -.397, 1.383))
    views = {
        "full": (Vector((0.0, -3.75, 1.02)), Vector((0.0, -.02, 1.0)), 66.0, (900, 1000)),
        "contact_front": (Vector((.72, -1.48, 1.49)), focus, 105.0, (1200, 900)),
        "contact_oblique": (Vector((.86, -.92, 1.66)), focus, 110.0, (1200, 900)),
        "contact_player": (Vector((-.18, -.92, 1.58)), focus, 108.0, (1200, 900)),
    }
    renders = {label: render(scene, camera, RENDERS / f"v301_{label}.png", *settings) for label, settings in views.items()}
    max_error = max(result["surface_errors_m"][digit] for digit in CONTACTS)
    status = "VISUAL_REVIEW_REQUIRED" if max_error <= .008 else "REJECT_CONTACT_ERROR"
    scene["V301_STATUS"] = status
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v301-global-continuous-fretting-v1",
        "status": status,
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)},
        "targets": {name: [float(v) for v in value] for name, value in targets.items()},
        "solve": result,
        "renders": renders,
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha(OUTPUT)},
    }
    (AUDIT / "v301_global_continuous_fretting.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V301_GLOBAL_CONTINUOUS_FRETTING_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
