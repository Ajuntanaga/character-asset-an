"""Replace failed transferred eyelid/phoneme shapes with donor-local correctives."""

from pathlib import Path
import hashlib
import json
import math

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v274h_identity_expression_proof" / "Character_An_identity_expression_proof_v274h.blend"
STAGE = ROOT / "production_v274i_corrected_identity_controls"
OUTPUT = STAGE / "Character_An_corrected_identity_controls_v274i.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"
DONOR = "V216_REFERENCE_FITTED_HEAD"
DRIVER = "V276E_GEO-head_animation_realistic"


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            digest.update(block)
    return digest.hexdigest()


def point_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def clear_controls(keys):
    for key in keys:
        if key.name.startswith("CTRL_"):
            key.value = 0.0
    bpy.context.view_layer.update()


def set_world(shape_point, matrix_inverse, world):
    shape_point.co = matrix_inverse @ world


def correct_blink(donor, name, center_x):
    basis = donor.data.shape_keys.key_blocks["Basis"]
    shape = donor.data.shape_keys.key_blocks[name]
    matrix = donor.matrix_world
    inverse = matrix.inverted()
    moved = 0
    maximum = 0.0
    for base_point, point in zip(basis.data, shape.data):
        world = matrix @ base_point.co
        point.co = base_point.co
        if world.y > -0.086:
            continue
        dx = (world.x - center_x) / 0.044
        dz = (world.z - 1.681) / 0.030
        weight = math.exp(-3.4 * (dx * dx + dz * dz))
        if weight < 0.015:
            continue
        corrected = world.copy()
        corrected.z += (1.681 - corrected.z) * min(0.96, weight * 1.12)
        # Bring the lid seam just in front of the eyeball instead of pulling it
        # back through the sclera.
        corrected.y = min(corrected.y, -0.112 - 0.0015 * weight)
        displacement = (corrected - world).length
        set_world(point, inverse, corrected)
        moved += 1
        maximum = max(maximum, displacement)
    return {"moved_vertices": moved, "max_displacement_m": maximum}


def mouth_weight(world):
    if world.y > -0.098 or not (1.558 < world.z < 1.638) or abs(world.x) > 0.072:
        return 0.0
    dx = world.x / 0.070
    dz = (world.z - 1.5985) / 0.044
    radial = math.exp(-2.65 * (dx * dx + dz * dz))
    front = min(1.0, max(0.0, (-0.098 - world.y) / 0.050))
    return radial * front


def correct_phoneme(donor, name, mode):
    basis = donor.data.shape_keys.key_blocks["Basis"]
    shape = donor.data.shape_keys.key_blocks[name]
    matrix = donor.matrix_world
    inverse = matrix.inverted()
    moved = 0
    maximum = 0.0
    for base_point, point in zip(basis.data, shape.data):
        world = matrix @ base_point.co
        point.co = base_point.co
        weight = mouth_weight(world)
        if weight < 0.02:
            continue
        corrected = world.copy()
        if mode == "M":
            corrected.z += (1.5985 - corrected.z) * min(0.92, weight * 1.28)
            corrected.y += 0.0018 * weight
        elif mode == "O":
            corrected.x += -corrected.x * 0.36 * weight
            corrected.z = 1.5985 + (corrected.z - 1.5985) * (1.0 + 0.52 * weight)
            corrected.y -= 0.0045 * weight
        elif mode == "E":
            corrected.x *= 1.0 + 0.19 * weight
            corrected.z += (1.5985 - corrected.z) * 0.22 * weight
            corrected.y -= 0.0015 * weight
        displacement = (corrected - world).length
        set_world(point, inverse, corrected)
        moved += 1
        maximum = max(maximum, displacement)
    return {"moved_vertices": moved, "max_displacement_m": maximum, "mode": mode}


def refine_hair():
    hair = bpy.data.objects["V217_TIGHT_CURL_GROOM"]
    hair.data.bevel_depth = 0.00042
    for spline in hair.data.splines:
        points = spline.points
        last = max(1, len(points) - 1)
        for index, point in enumerate(points):
            t = index / last
            # Soft root plus a narrow terminal tip removes the clipped wire ends.
            point.radius = 0.68 + 0.42 * math.sin(math.pi * t)
            if t > 0.72:
                point.radius *= max(0.08, (1.0 - t) / 0.28)
    return {"splines": len(hair.data.splines), "bevel_depth_m": hair.data.bevel_depth, "tapered": True}


def render_pose(scene, keys, label, controls):
    clear_controls(keys)
    for name, value in controls.items():
        keys[name].value = value
    bpy.context.view_layer.update()
    path = RENDERS / f"v274i_{label}.png"
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(path), "controls": controls}


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    for folder in (STAGE, RENDERS, AUDIT):
        folder.mkdir(parents=True, exist_ok=True)
    donor = bpy.data.objects[DONOR]
    driver = bpy.data.objects[DRIVER]
    corrections = {
        "CTRL_Blink_L": correct_blink(donor, "CTRL_Blink_L", 0.035),
        "CTRL_Blink_R": correct_blink(donor, "CTRL_Blink_R", -0.035),
        "CTRL_Phoneme_O": correct_phoneme(donor, "CTRL_Phoneme_O", "O"),
        "CTRL_Phoneme_E": correct_phoneme(donor, "CTRL_Phoneme_E", "E"),
        "CTRL_Phoneme_M": correct_phoneme(donor, "CTRL_Phoneme_M", "M"),
    }
    hair_record = refine_hair()
    scene = bpy.context.scene
    scene.render.resolution_x = 768
    scene.render.resolution_y = 768
    camera = bpy.data.objects["V276E_CAMERA"]
    scene.camera = camera
    camera.location = Vector((0.0, -1.47, 1.67))
    camera.data.lens = 96.0
    point_at(camera, Vector((0.0, -0.035, 1.655)))
    keys = driver.data.shape_keys.key_blocks
    poses = {
        "neutral": {},
        "blink": {"CTRL_Blink_L": 1.0, "CTRL_Blink_R": 1.0},
        "smile": {"CTRL_Smile": 1.0},
        "jaw_open": {"CTRL_JawOpen": 0.72},
        "phoneme_o": {"CTRL_Phoneme_O": 1.0, "CTRL_JawOpen": 0.16},
        "phoneme_e": {"CTRL_Phoneme_E": 1.0},
        "phoneme_m": {"CTRL_Phoneme_M": 1.0},
    }
    renders = {label: render_pose(scene, keys, label, controls) for label, controls in poses.items()}
    clear_controls(keys)
    neutral_values = {key.name: key.value for key in keys if key.name.startswith("CTRL_")}
    neutral_return = max(abs(value) for value in neutral_values.values())
    scene["V274I_STATUS"] = "CORRECTED_IDENTITY_CONTROLS_VISUAL_REVIEW_REQUIRED"
    scene["V274I_NEUTRAL_RETURN_MAX_CONTROL"] = neutral_return
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v274i-corrected-identity-controls-v1",
        "status": "BUILT_VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)},
        "correctives": corrections,
        "hair": hair_record,
        "renders": renders,
        "neutral_return_max_control": neutral_return,
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha(OUTPUT)},
    }
    (AUDIT / "v274i_corrected_identity_controls.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V274I_CORRECTED_IDENTITY_CONTROLS_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
