"""Surface-lock the fretting pads while optimizing the visible finger arcs."""

from pathlib import Path
import hashlib
import json

import bpy
from mathutils import Matrix, Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v294_pick_string_alignment" / "Character_An_pick_string_alignment_v294.blend"
STAGE = ROOT / "production_v297_surface_locked_fretting"
OUTPUT = STAGE / "Character_An_surface_locked_fretting_v297.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"
RIG = "V250_FRETTING_HAND_RIG"
HAND = "V248_FRETTING_HAND_REALISTIC"
NECK = "V206_NECK"

# Validated exposed pad vertices and the authoritative string/fret locations.
CONTACTS = {
    "index": (234, 0.3058091, 0.0041983, "S5", 9),
    "middle": (211, 0.3296208, -0.0042574, "S4", 10),
    "ring": (14, 0.3050833, 0.0209915, "S7", 9),
    "pinky": (225, 0.3488616, 0.0301914, "S8", 11),
}


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
            t = (x - a.x) / (b.x - a.x)
            return a.z + t * (b.z - a.z)
    return min(points, key=lambda point: abs(point.x - x)).z


def surface_world(hand, vertex_index):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = hand.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    try:
        return evaluated.matrix_world @ mesh.vertices[vertex_index].co
    finally:
        evaluated.to_mesh_clear()


def target_world(neck, vertex_spec):
    _vertex, x, y, string_id, _fret = vertex_spec
    string_obj = bpy.data.objects[f"V206_STRING_{string_id}"]
    radius = float(string_obj.data.bevel_depth)
    z = string_z_at_x(string_obj, x) - 0.00185 + radius
    return neck.matrix_world @ Vector((x, y, z))


def arc_samples(rig, digit):
    """Sample only the non-contact arc; the distal pad must enter the string plane."""
    result = []
    for joint in (1, 2):
        bone = rig.pose.bones[f"{digit}_{joint:02d}"]
        head = rig.matrix_world @ bone.head
        tail = rig.matrix_world @ bone.tail
        result.extend((head, head.lerp(tail, .33), head.lerp(tail, .66), tail))
    distal = rig.pose.bones[f"{digit}_03"]
    head = rig.matrix_world @ distal.head
    tail = rig.matrix_world @ distal.tail
    result.extend((head, head.lerp(tail, .35)))
    return result


def penetration(neck, point):
    local = neck.matrix_world.inverted() @ point
    if not (-.035 < local.x < .610 and abs(local.y) < .055 and -.039 < local.z < .019):
        return 0.0, local
    depths = (
        local.x + .035,
        .610 - local.x,
        .055 - abs(local.y),
        local.z + .039,
        .019 - local.z,
    )
    return min(depths) + .003, local


def clearance_metrics(rig, neck, digit):
    samples = arc_samples(rig, digit)
    measured = [penetration(neck, point) for point in samples]
    return {
        "inside_samples": sum(depth > 0.0 for depth, _local in measured),
        "penalty": float(sum(depth * depth for depth, _local in measured)),
        "samples_neck_local": [[round(float(v), 6) for v in local] for _depth, local in measured],
    }


def project_surface(rig, hand, digit, vertex_index, target, base_origin, max_translation=.030):
    root = rig.pose.bones[f"{digit}_01"]
    epsilon = .00012
    for _iteration in range(5):
        current = surface_world(hand, vertex_index)
        error = target - current
        if error.length < .00008:
            break
        base = root.location.copy()
        columns = []
        for axis in range(3):
            root.location = base.copy()
            root.location[axis] += epsilon
            bpy.context.view_layer.update()
            columns.append((surface_world(hand, vertex_index) - current) / epsilon)
        root.location = base
        bpy.context.view_layer.update()
        jacobian = Matrix((columns[0], columns[1], columns[2])).transposed()
        try:
            delta = jacobian.inverted() @ error
        except ValueError:
            break
        if delta.length > .012:
            delta.normalize()
            delta *= .012
        root.location += delta
        offset = root.location - base_origin
        if offset.length > max_translation:
            offset.normalize()
            root.location = base_origin + offset * max_translation
        bpy.context.view_layer.update()
    return (surface_world(hand, vertex_index) - target).length


def solve_digit(rig, hand, neck, digit, vertex_index, target):
    bones = [rig.pose.bones[f"{digit}_{joint:02d}"] for joint in range(1, 4)]
    for bone in bones:
        bone.rotation_mode = "XYZ"
    base_origin = bones[0].location.copy()
    original_rotations = [bone.rotation_euler.copy() for bone in bones]
    variables = [
        (bones[0], 0, -.50, .95),
        (bones[0], 1, -.85, .85),
        (bones[0], 2, -.85, .85),
        (bones[1], 0, -.12, 1.35),
        (bones[1], 1, -.35, .35),
        (bones[2], 0, -.12, 1.10),
        (bones[2], 1, -.28, .28),
    ]

    project_surface(rig, hand, digit, vertex_index, target, base_origin)
    before = clearance_metrics(rig, neck, digit)

    def objective():
        contact_error = (surface_world(hand, vertex_index) - target).length
        clearance = clearance_metrics(rig, neck, digit)
        translation = (bones[0].location - base_origin).length
        rotation_delta = sum(
            (float(bone.rotation_euler[axis]) - float(original_rotations[index][axis])) ** 2
            for index, bone in enumerate(bones)
            for axis in range(3)
        )
        return (
            clearance["penalty"] * 420.0
            + contact_error * contact_error * 12000.0
            + translation * translation * 2.0
            + rotation_delta * .000010
        )

    best = objective()
    evaluations = 1
    for step in (.26, .14, .075, .038, .019, .0095):
        for _pass in range(4):
            improved = False
            for bone, axis, lower, upper in variables:
                saved_rotations = [item.rotation_euler.copy() for item in bones]
                saved_location = bones[0].location.copy()
                base_value = float(bone.rotation_euler[axis])
                local_best = best
                accepted = None
                for candidate in (max(lower, base_value - step), min(upper, base_value + step)):
                    for item, saved in zip(bones, saved_rotations):
                        item.rotation_euler = saved.copy()
                    bones[0].location = saved_location.copy()
                    bone.rotation_euler[axis] = candidate
                    bpy.context.view_layer.update()
                    error = project_surface(rig, hand, digit, vertex_index, target, base_origin)
                    value = objective() if error < .0012 else 1e9 + error
                    evaluations += 1
                    if value < local_best:
                        local_best = value
                        accepted = ([item.rotation_euler.copy() for item in bones], bones[0].location.copy())
                if accepted is None:
                    for item, saved in zip(bones, saved_rotations):
                        item.rotation_euler = saved.copy()
                    bones[0].location = saved_location.copy()
                    bpy.context.view_layer.update()
                else:
                    accepted_rotations, accepted_location = accepted
                    for item, saved in zip(bones, accepted_rotations):
                        item.rotation_euler = saved.copy()
                    bones[0].location = accepted_location
                    bpy.context.view_layer.update()
                    best = local_best
                    improved = True
            if not improved:
                break
    final_error = project_surface(rig, hand, digit, vertex_index, target, base_origin)
    after = clearance_metrics(rig, neck, digit)
    return {
        "evaluations": evaluations,
        "surface_vertex": vertex_index,
        "target_world": [float(v) for v in target],
        "surface_world": [float(v) for v in surface_world(hand, vertex_index)],
        "surface_error_m": float(final_error),
        "base_translation_m": [float(v) for v in bones[0].location],
        "translation_delta_m": float((bones[0].location - base_origin).length),
        "before": before,
        "after": after,
        "rotations_xyz_rad": {bone.name: [float(v) for v in bone.rotation_euler] for bone in bones},
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
    neck = bpy.data.objects[NECK]
    solves = {}
    for digit, spec in CONTACTS.items():
        vertex_index, _x, _y, string_id, fret = spec
        target = target_world(neck, spec)
        solves[digit] = solve_digit(rig, hand, neck, digit, vertex_index, target)
        solves[digit].update({"string": string_id, "fret": fret, "depression_m": .00185})
    bpy.context.view_layer.update()

    scene = bpy.context.scene
    camera = bpy.data.objects["V287_GUITAR_CAMERA"]
    focus = Vector((.262, -.397, 1.383))
    views = {
        "full": (Vector((0.0, -3.75, 1.02)), Vector((0.0, -.02, 1.0)), 66.0, (900, 1000)),
        "contact_front": (Vector((.72, -1.48, 1.49)), focus, 105.0, (1200, 900)),
        "contact_oblique": (Vector((.86, -.92, 1.66)), focus, 110.0, (1200, 900)),
        "contact_low": (Vector((.55, -.86, 1.20)), focus, 105.0, (1200, 900)),
    }
    renders = {
        label: render(scene, camera, RENDERS / f"v297_{label}.png", *settings)
        for label, settings in views.items()
    }
    max_error = max(item["surface_error_m"] for item in solves.values())
    total_inside = sum(item["after"]["inside_samples"] for item in solves.values())
    status = "VISUAL_REVIEW_REQUIRED" if max_error <= .0012 else "REJECT_CONTACT_ERROR"
    scene["V297_STATUS"] = status
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v297-surface-locked-fretting-v1",
        "status": status,
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)},
        "max_surface_error_m": max_error,
        "total_proximal_inside_samples": total_inside,
        "solves": solves,
        "renders": renders,
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha(OUTPUT)},
    }
    (AUDIT / "v297_surface_locked_fretting.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V297_SURFACE_LOCKED_FRETTING_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
