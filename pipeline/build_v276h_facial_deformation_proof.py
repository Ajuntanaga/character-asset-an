"""Prove blink, jaw, smile, and brow deformation on the animation topology."""

from pathlib import Path
import hashlib, json, math
import bpy
from mathutils import Matrix, Vector

ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v276g_landmark_identity" / "Character_An_landmark_identity_v276g.blend"
STAGE = ROOT / "production_v276h_facial_deformation_proof"
OUTPUT = STAGE / "Character_An_facial_deformation_v276h.blend"
RENDERS, AUDIT = STAGE / "renders", STAGE / "audit"
HEAD, JAW = "V276E_GEO-head_animation_realistic", "V276E_Jaw - Realistic"


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            h.update(block)
    return h.hexdigest()


def smoothstep(a, b, value):
    t = max(0.0, min(1.0, (value - a) / (b - a)))
    return t * t * (3.0 - 2.0 * t)


def gaussian(value, center, radius):
    return math.exp(-((value - center) / radius) ** 2)


def add_relative_shape(head, identity, name, deform):
    for key in head.data.shape_keys.key_blocks:
        if key.name != identity.name:
            key.value = 0.0
    identity.value = 1.0
    bpy.context.view_layer.update()
    key = head.shape_key_add(name=name, from_mix=True)
    key.relative_key = identity
    moved, maximum = 0, 0.0
    for point in key.data:
        world = head.matrix_world @ point.co
        destination = deform(world)
        distance = (destination - world).length
        if distance > 1e-7:
            point.co = head.matrix_world.inverted() @ destination
            moved += 1
            maximum = max(maximum, distance)
    key.value = 0.0
    return key, {"moved_vertices": moved, "max_displacement_m": maximum}


def blink(side):
    cx = 0.035 if side == "L" else -0.035
    seam = 1.675
    def deform(point):
        if abs(point.x - cx) > 0.030 or abs(point.z - seam) > 0.025 or point.y > -0.090:
            return point
        lateral = gaussian(point.x, cx, 0.022)
        vertical = gaussian(point.z, seam, 0.020)
        front = smoothstep(-0.085, -0.115, point.y)
        weight = lateral * vertical * front
        closure = min(1.0, weight * 1.6)
        return point + Vector((0.0, 0.0040 * closure, (seam - point.z) * closure))
    return deform


def jaw_open(point):
    pivot = Vector((0.0, -0.005, 1.605))
    lower = smoothstep(1.605, 1.505, point.z)
    front = 1.0 - smoothstep(0.02, 0.105, point.y)
    lateral = 1.0 - smoothstep(0.105, 0.150, abs(point.x))
    weight = lower * front * lateral
    angle = math.radians(13.0) * weight
    relative = point - pivot
    rotated = Matrix.Rotation(angle, 4, "X") @ relative
    return pivot + rotated


def smile(point):
    vertical = gaussian(point.z, 1.572, 0.032)
    front = smoothstep(-0.085, -0.120, point.y)
    side = smoothstep(0.018, 0.050, abs(point.x)) * (1.0 - smoothstep(0.060, 0.095, abs(point.x)))
    weight = vertical * front * side
    return point + Vector(((0.010 if point.x >= 0 else -0.010) * weight, -0.001 * weight, 0.009 * weight))


def brow_raise(point):
    vertical = gaussian(point.z, 1.712, 0.025)
    front = smoothstep(-0.075, -0.110, point.y)
    lateral = gaussian(abs(point.x), 0.043, 0.035)
    weight = vertical * front * lateral
    return point + Vector((0.0, -0.001 * weight, 0.010 * weight))


def point_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def main():
    if Path(bpy.data.filepath).resolve() != SOURCE.resolve():
        raise RuntimeError(f"Open V276G first: {SOURCE}")
    for folder in (STAGE, RENDERS, AUDIT):
        folder.mkdir(parents=True, exist_ok=True)
    head, jaw = bpy.data.objects[HEAD], bpy.data.objects[JAW]
    identity = head.data.shape_keys.key_blocks["IDENTITY_LANDMARK_WARP"]
    records = {}
    controls = {}
    for name, deform in (
        ("CTRL_Blink_L", blink("L")),
        ("CTRL_Blink_R", blink("R")),
        ("CTRL_JawOpen", jaw_open),
        ("CTRL_Smile", smile),
        ("CTRL_BrowRaise", brow_raise),
    ):
        key, record = add_relative_shape(head, identity, name, deform)
        controls[name] = key
        records[name] = record

    pivot = bpy.data.objects.new("V276H_JAW_HINGE", None)
    bpy.context.scene.collection.objects.link(pivot)
    pivot.location = Vector((0.0, -0.005, 1.605))
    world = jaw.matrix_world.copy()
    jaw.parent = pivot
    jaw.matrix_parent_inverse = pivot.matrix_world.inverted()
    jaw.matrix_world = world

    scene, cam = bpy.context.scene, bpy.data.objects["V276E_CAMERA"]
    cam.location = Vector((0.0, -2.05, 1.605))
    cam.data.lens = 96
    point_at(cam, Vector((0.0, -0.005, 1.605)))
    scene.camera = cam
    scene.render.resolution_x, scene.render.resolution_y = 800, 900
    scene.render.resolution_percentage = 100
    tests = {
        "neutral": ({}, 0.0),
        "blink": ({"CTRL_Blink_L": 1.0, "CTRL_Blink_R": 1.0}, 0.0),
        "left_blink": ({"CTRL_Blink_L": 1.0}, 0.0),
        "jaw_open": ({"CTRL_JawOpen": 1.0}, math.radians(13.0)),
        "smile": ({"CTRL_Smile": 1.0, "CTRL_BrowRaise": 0.12}, 0.0),
        "brow_raise": ({"CTRL_BrowRaise": 1.0}, 0.0),
    }
    render_records = {}
    for label, (values, jaw_angle) in tests.items():
        for name, key in controls.items():
            key.value = values.get(name, 0.0)
        pivot.rotation_euler = (jaw_angle, 0.0, 0.0)
        bpy.context.view_layer.update()
        path = RENDERS / f"v276h_{label}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        render_records[label] = {"path": str(path.relative_to(ROOT)), "values": values, "jaw_angle_degrees": math.degrees(jaw_angle)}

    scene.frame_start, scene.frame_end = 1, 60
    sequence = [(1, "neutral"), (10, "blink"), (20, "left_blink"), (30, "jaw_open"), (40, "smile"), (50, "brow_raise"), (60, "neutral")]
    for frame, label in sequence:
        values, jaw_angle = tests[label]
        for name, key in controls.items():
            key.value = values.get(name, 0.0)
            key.keyframe_insert(data_path="value", frame=frame)
        pivot.rotation_euler = (jaw_angle, 0.0, 0.0)
        pivot.keyframe_insert(data_path="rotation_euler", frame=frame)
    scene.frame_set(1)
    scene["V276H_STATUS"] = "FACIAL_DEFORMATION_PROOF_VISUAL_REVIEW_REQUIRED"
    scene["V276H_CONTROLS"] = ",".join(controls)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v276h-facial-deformation-proof-v1",
        "status": "BUILT_VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)},
        "controls": records,
        "jaw_hinge": {"object": pivot.name, "pivot": list(pivot.location)},
        "sequence": sequence,
        "renders": render_records,
        "output": {"path": str(OUTPUT.relative_to(ROOT))},
    }
    record["output"]["sha256"] = sha(OUTPUT)
    (AUDIT / "v276h_facial_deformation.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V276H_FACIAL_DEFORMATION_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
