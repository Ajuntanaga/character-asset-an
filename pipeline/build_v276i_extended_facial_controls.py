"""Add gaze, frown, lip-seal, and phoneme controls to V276H."""

from pathlib import Path
import hashlib, json, math
import bpy
from mathutils import Vector

ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v276h_facial_deformation_proof" / "Character_An_facial_deformation_v276h.blend"
STAGE = ROOT / "production_v276i_extended_facial_controls"
OUTPUT = STAGE / "Character_An_extended_facial_controls_v276i.blend"
RENDERS, AUDIT = STAGE / "renders", STAGE / "audit"
HEAD = "V276E_GEO-head_animation_realistic"


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


def add_shape(head, identity, name, deform):
    for key in head.data.shape_keys.key_blocks:
        key.value = 1.0 if key == identity else 0.0
    bpy.context.view_layer.update()
    key = head.shape_key_add(name=name, from_mix=True)
    key.relative_key = identity
    inverse = head.matrix_world.inverted()
    moved, maximum = 0, 0.0
    for point in key.data:
        world = head.matrix_world @ point.co
        destination = deform(world)
        distance = (destination - world).length
        if distance > 1e-7:
            point.co = inverse @ destination
            moved += 1
            maximum = max(maximum, distance)
    key.value = 0.0
    return key, {"moved_vertices": moved, "max_displacement_m": maximum}


def lip_weight(point):
    return gaussian(point.z, 1.568, 0.030) * smoothstep(-0.080, -0.115, point.y) * (1.0 - smoothstep(0.075, 0.105, abs(point.x)))


def frown(point):
    weight = lip_weight(point) * smoothstep(0.018, 0.045, abs(point.x))
    return point + Vector(((-0.004 if point.x >= 0 else 0.004) * weight, 0.001 * weight, -0.008 * weight))


def phoneme_o(point):
    weight = lip_weight(point)
    return point + Vector((-point.x * 0.28 * weight, -0.010 * weight, (1.568 - point.z) * 0.28 * weight))


def phoneme_e(point):
    weight = lip_weight(point)
    return point + Vector(((0.010 if point.x >= 0 else -0.010) * weight, 0.001 * weight, (1.568 - point.z) * 0.18 * weight))


def phoneme_m(point):
    weight = lip_weight(point)
    seam = 1.570
    overlap = -0.0006 if point.z >= seam else 0.0006
    return point + Vector((0.0, 0.0015 * weight, (seam + overlap - point.z) * 0.72 * weight))


def cheek_puff(point):
    side = gaussian(abs(point.x), 0.075, 0.035)
    vertical = gaussian(point.z, 1.610, 0.055)
    front = smoothstep(-0.045, -0.095, point.y)
    weight = side * vertical * front
    return point + Vector(((0.006 if point.x >= 0 else -0.006) * weight, -0.008 * weight, 0.001 * weight))


def point_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def main():
    if Path(bpy.data.filepath).resolve() != SOURCE.resolve():
        raise RuntimeError(f"Open V276H first: {SOURCE}")
    for folder in (STAGE, RENDERS, AUDIT):
        folder.mkdir(parents=True, exist_ok=True)
    head = bpy.data.objects[HEAD]
    keys = head.data.shape_keys.key_blocks
    identity = keys["IDENTITY_LANDMARK_WARP"]
    additions, records = {}, {}
    for name, deform in (
        ("CTRL_Frown", frown),
        ("CTRL_Phoneme_O", phoneme_o),
        ("CTRL_Phoneme_E", phoneme_e),
        ("CTRL_Phoneme_M", phoneme_m),
        ("CTRL_CheekPuff", cheek_puff),
    ):
        key, record = add_shape(head, identity, name, deform)
        additions[name], records[name] = key, record
    for key in keys:
        key.value = 1.0 if key == identity else 0.0

    eyes = {
        side: bpy.data.objects[f"V276E_GEO-head_animation_realistic.sclera.{side}"]
        for side in ("L", "R")
    }
    for eye in eyes.values():
        eye.rotation_mode = "XYZ"
        eye.rotation_euler = (0.0, 0.0, 0.0)

    scene, cam = bpy.context.scene, bpy.data.objects["V276E_CAMERA"]
    cam.location = Vector((0.0, -2.05, 1.605))
    cam.data.lens = 100
    point_at(cam, Vector((0.0, -0.005, 1.605)))
    scene.camera = cam
    scene.render.resolution_x, scene.render.resolution_y = 800, 900
    scene.render.resolution_percentage = 100
    tests = {
        "neutral": ({}, (0.0, 0.0, 0.0)),
        "gaze_left": ({}, (0.0, 0.0, math.radians(12))),
        "gaze_up": ({}, (math.radians(-9), 0.0, 0.0)),
        "frown": ({"CTRL_Frown": 1.0}, (0.0, 0.0, 0.0)),
        "phoneme_o": ({"CTRL_Phoneme_O": 1.0}, (0.0, 0.0, 0.0)),
        "phoneme_e": ({"CTRL_Phoneme_E": 1.0}, (0.0, 0.0, 0.0)),
        "phoneme_m": ({"CTRL_Phoneme_M": 1.0}, (0.0, 0.0, 0.0)),
        "cheek_puff": ({"CTRL_CheekPuff": 1.0}, (0.0, 0.0, 0.0)),
    }
    renders = {}
    for label, (values, rotation) in tests.items():
        for key in keys:
            key.value = 1.0 if key == identity else values.get(key.name, 0.0)
        for eye in eyes.values():
            eye.rotation_euler = rotation
        bpy.context.view_layer.update()
        path = RENDERS / f"v276i_{label}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        renders[label] = {"path": str(path.relative_to(ROOT)), "values": values, "eye_rotation_degrees": [math.degrees(v) for v in rotation]}

    sequence = [(70, "gaze_left"), (80, "gaze_up"), (90, "frown"), (100, "phoneme_o"), (110, "phoneme_e"), (120, "phoneme_m"), (130, "cheek_puff"), (140, "neutral")]
    scene.frame_end = 140
    for frame, label in sequence:
        values, rotation = tests[label]
        for key in additions.values():
            key.value = values.get(key.name, 0.0)
            key.keyframe_insert(data_path="value", frame=frame)
        for eye in eyes.values():
            eye.rotation_euler = rotation
            eye.keyframe_insert(data_path="rotation_euler", frame=frame)
    scene.frame_set(1)
    for key in keys:
        key.value = 1.0 if key == identity else 0.0
    for eye in eyes.values():
        eye.rotation_euler = (0.0, 0.0, 0.0)
    scene["V276I_STATUS"] = "EXTENDED_FACIAL_CONTROLS_VISUAL_REVIEW_REQUIRED"
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v276i-extended-facial-controls-v1",
        "status": "BUILT_VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)},
        "controls": records,
        "gaze_objects": [eye.name for eye in eyes.values()],
        "sequence": sequence,
        "renders": renders,
        "output": {"path": str(OUTPUT.relative_to(ROOT))},
    }
    record["output"]["sha256"] = sha(OUTPUT)
    (AUDIT / "v276i_extended_facial_controls.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V276I_EXTENDED_CONTROLS_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
