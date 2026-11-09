"""Build corrected gaze and speech controls from the accepted V276H face proof."""

from pathlib import Path
import hashlib
import json
import math

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v276h_facial_deformation_proof" / "Character_An_facial_deformation_v276h.blend"
STAGE = ROOT / "production_v276j_corrected_facial_controls"
OUTPUT = STAGE / "Character_An_corrected_facial_controls_v276j.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"
HEAD = "V276E_GEO-head_animation_realistic"


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            digest.update(block)
    return digest.hexdigest()


def smoothstep(a, b, value):
    t = max(0.0, min(1.0, (value - a) / (b - a)))
    return t * t * (3.0 - 2.0 * t)


def gaussian(value, center, radius):
    return math.exp(-((value - center) / radius) ** 2)


def mouth_mask(point, vertical_radius=0.016, lateral_limit=0.074):
    if abs(point.x) > lateral_limit or point.z < 1.548 or point.z > 1.590:
        return 0.0
    vertical = gaussian(point.z, 1.569, vertical_radius)
    depth = gaussian(point.y, -0.125, 0.020)
    return vertical * depth


def add_shape(head, identity, name, deform):
    for key in head.data.shape_keys.key_blocks:
        key.value = 1.0 if key == identity else 0.0
    bpy.context.view_layer.update()
    key = head.shape_key_add(name=name, from_mix=True)
    key.relative_key = identity
    inverse = head.matrix_world.inverted()
    moved = 0
    maximum = 0.0
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


def frown(point):
    weight = mouth_mask(point, 0.015) * smoothstep(0.024, 0.047, abs(point.x))
    return point + Vector(((-0.0035 if point.x >= 0 else 0.0035) * weight, 0.0005 * weight, -0.0060 * weight))


def phoneme_o(point):
    weight = mouth_mask(point, 0.017, 0.070)
    if not weight:
        return point
    return point + Vector((-point.x * 0.30 * weight, -0.0060 * weight, (1.569 - point.z) * 0.12 * weight))


def phoneme_e(point):
    weight = mouth_mask(point, 0.015, 0.078)
    if not weight:
        return point
    corner = smoothstep(0.018, 0.045, abs(point.x))
    return point + Vector(((0.0060 if point.x >= 0 else -0.0060) * weight * corner, -0.0008 * weight, (1.569 - point.z) * 0.10 * weight))


def phoneme_m(point):
    if abs(point.x) > 0.068 or point.z < 1.553 or point.z > 1.585:
        return point
    weight = gaussian(point.z, 1.569, 0.012) * gaussian(point.y, -0.126, 0.017)
    if point.z >= 1.569:
        target_z = 1.5687
    else:
        target_z = 1.5683
    return point + Vector((0.0, -0.0010 * weight, (target_z - point.z) * 0.92 * weight))


def cheek_puff(point):
    if abs(point.x) < 0.038 or abs(point.x) > 0.110 or point.z < 1.555 or point.z > 1.670 or point.y > -0.065:
        return point
    side = gaussian(abs(point.x), 0.073, 0.026)
    vertical = gaussian(point.z, 1.612, 0.041)
    depth = gaussian(point.y, -0.099, 0.032)
    weight = side * vertical * depth
    return point + Vector(((0.010 if point.x >= 0 else -0.010) * weight, -0.012 * weight, 0.0010 * weight))


def point_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def add_gaze_control(eyes):
    control = bpy.data.objects.new("CTRL_FACE_GAZE", None)
    bpy.context.scene.collection.objects.link(control)
    control.empty_display_type = "CIRCLE"
    control.empty_display_size = 0.035
    control.location = Vector((0.0, -0.155, 1.681))
    control.hide_render = True
    control["gaze_horizontal"] = 0.0
    control["gaze_vertical"] = 0.0
    control.id_properties_ui("gaze_horizontal").update(min=-30.0, max=30.0, soft_min=-25.0, soft_max=25.0)
    control.id_properties_ui("gaze_vertical").update(min=-20.0, max=20.0, soft_min=-15.0, soft_max=15.0)
    for eye in eyes.values():
        eye.rotation_mode = "XYZ"
        for index, prop in ((0, "gaze_vertical"), (2, "gaze_horizontal")):
            curve = eye.driver_add("rotation_euler", index)
            variable = curve.driver.variables.new()
            variable.name = "gaze"
            variable.type = "SINGLE_PROP"
            variable.targets[0].id = control
            variable.targets[0].data_path = f'["{prop}"]'
            curve.driver.expression = "gaze * 0.017453292519943295"
    return control


def main():
    if Path(bpy.data.filepath).resolve() != SOURCE.resolve():
        raise RuntimeError(f"Open V276H first: {SOURCE}")
    for folder in (STAGE, RENDERS, AUDIT):
        folder.mkdir(parents=True, exist_ok=True)

    head = bpy.data.objects[HEAD]
    keys = head.data.shape_keys.key_blocks
    identity = keys["IDENTITY_LANDMARK_WARP"]
    additions = {}
    records = {}
    for name, deform in (
        ("CTRL_Frown", frown),
        ("CTRL_Phoneme_O", phoneme_o),
        ("CTRL_Phoneme_E", phoneme_e),
        ("CTRL_Phoneme_M", phoneme_m),
        ("CTRL_CheekPuff", cheek_puff),
    ):
        key, record = add_shape(head, identity, name, deform)
        additions[name] = key
        records[name] = record

    for key in keys:
        key.value = 1.0 if key == identity else 0.0
    eyes = {side: bpy.data.objects[f"V276E_GEO-head_animation_realistic.sclera.{side}"] for side in ("L", "R")}
    gaze = add_gaze_control(eyes)

    scene = bpy.context.scene
    camera = bpy.data.objects["V276E_CAMERA"]
    camera.location = Vector((0.0, -2.05, 1.615))
    camera.data.lens = 105
    point_at(camera, Vector((0.0, -0.010, 1.615)))
    scene.camera = camera
    scene.render.resolution_x = 900
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100

    tests = {
        "neutral": ({}, 0.0, 0.0),
        "gaze_left": ({}, 24.0, 0.0),
        "gaze_up": ({}, 0.0, -17.0),
        "frown": ({"CTRL_Frown": 1.0}, 0.0, 0.0),
        "phoneme_o": ({"CTRL_Phoneme_O": 1.0}, 0.0, 0.0),
        "phoneme_e": ({"CTRL_Phoneme_E": 1.0}, 0.0, 0.0),
        "phoneme_m": ({"CTRL_Phoneme_M": 1.0}, 0.0, 0.0),
        "cheek_puff": ({"CTRL_CheekPuff": 1.0}, 0.0, 0.0),
    }
    render_records = {}
    for label, (values, horizontal, vertical) in tests.items():
        for key in keys:
            key.value = 1.0 if key == identity else values.get(key.name, 0.0)
        gaze["gaze_horizontal"] = horizontal
        gaze["gaze_vertical"] = vertical
        bpy.context.view_layer.update()
        path = RENDERS / f"v276j_{label}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        render_records[label] = {
            "path": str(path.relative_to(ROOT)),
            "values": values,
            "gaze_degrees": [horizontal, vertical],
        }

    if head.data.shape_keys.animation_data:
        head.data.shape_keys.animation_data_clear()
    gaze.animation_data_clear()
    sequence = [
        (1, "neutral"),
        (10, "gaze_left"),
        (20, "gaze_up"),
        (30, "frown"),
        (40, "phoneme_o"),
        (50, "phoneme_e"),
        (60, "phoneme_m"),
        (70, "cheek_puff"),
        (80, "neutral"),
    ]
    scene.frame_start = 1
    scene.frame_end = 80
    for frame, label in sequence:
        values, horizontal, vertical = tests[label]
        for key in additions.values():
            key.value = values.get(key.name, 0.0)
            key.keyframe_insert(data_path="value", frame=frame)
        gaze["gaze_horizontal"] = horizontal
        gaze["gaze_vertical"] = vertical
        gaze.keyframe_insert(data_path='["gaze_horizontal"]', frame=frame)
        gaze.keyframe_insert(data_path='["gaze_vertical"]', frame=frame)
    scene.frame_set(1)
    scene["V276J_STATUS"] = "CORRECTED_FACIAL_CONTROLS_VISUAL_REVIEW_REQUIRED"
    scene["V276J_GAZE_CONTROL"] = gaze.name
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)

    audit = {
        "schema": "v276j-corrected-facial-controls-v1",
        "status": "BUILT_VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)},
        "controls": records,
        "gaze_control": {"object": gaze.name, "properties": ["gaze_horizontal", "gaze_vertical"]},
        "sequence": sequence,
        "renders": render_records,
        "output": {"path": str(OUTPUT.relative_to(ROOT))},
    }
    audit["output"]["sha256"] = sha(OUTPUT)
    (AUDIT / "v276j_corrected_facial_controls.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    print("V276J_CORRECTED_CONTROLS_OK=" + json.dumps(audit, sort_keys=True))


if __name__ == "__main__":
    main()
