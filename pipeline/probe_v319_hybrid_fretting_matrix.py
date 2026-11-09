"""Probe FK-seeded Rigify finger IK against the authoritative visible chord."""

from pathlib import Path
import hashlib
import json
import math
import sys

import bpy
from mathutils import Matrix, Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v318_reference_guitar_rebuild" / "Character_An_reference_guitar_rebuild_v318.blend"
STAGE = ROOT / "production_v319_fretting_hand"
RENDERS = STAGE / "renders" / "probe"
AUDIT = STAGE / "audit"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.guitar_geometry import GuitarGeometry, load_authoritative_mapping


NEUTRAL_FRET_X = 0.260
CONTACT_Z = 0.02045
PAD_OFFSETS_M = {"index": 0.00535, "middle": 0.00555, "ring": 0.00525, "pinky": 0.00465}
VISIBLE_MAP = {
    "index": ("S6", 11, True),
    "middle": ("S6", 10, False),
    "ring": ("S7", 9, True),
    "pinky": ("S8", 11, True),
}
THUMB_TARGET = Vector((0.2470, -0.3150, 1.3720))
FLEX_AXES = {"index": "X", "middle": "Z", "ring": "X", "pinky": "X", "thumb": "X"}
LATERAL = {
    "index": ("Z", -1.0),
    "middle": ("X", 1.0),
    "ring": ("Z", 1.0),
    "pinky": ("Z", 1.0),
    "thumb": ("Z", -1.0),
}
CANDIDATES = {
    "A_light": {
        "hand_delta": (-0.030, 0.025, 0.005), "hand_roll": 0.0,
        "curl": (14.0, 24.0, 14.0), "spread": 8.0,
    },
    "B_medium": {
        "hand_delta": (-0.030, 0.025, 0.005), "hand_roll": 0.0,
        "curl": (23.0, 36.0, 21.0), "spread": 11.0,
    },
    "C_medium_roll10": {
        "hand_delta": (-0.030, 0.025, 0.005), "hand_roll": 10.0,
        "curl": (23.0, 36.0, 21.0), "spread": 11.0,
    },
    "D_strong_roll10": {
        "hand_delta": (-0.030, 0.025, 0.005), "hand_roll": 10.0,
        "curl": (31.0, 48.0, 28.0), "spread": 14.0,
    },
    "E_medium_no_spread": {
        "hand_delta": (-0.030, 0.025, 0.005), "hand_roll": 10.0,
        "curl": (23.0, 36.0, 21.0), "spread": 0.0,
    },
    "F_custom": {
        "hand_delta": (-0.026, 0.026, 0.004), "hand_roll": 7.0,
        "curl_by_digit": {
            "index": (28.0, 43.0, 24.0),
            "middle": (22.0, 34.0, 19.0),
            "ring": (27.0, 41.0, 24.0),
            "pinky": (32.0, 49.0, 29.0),
            "thumb": (18.0, 28.0, 18.0),
        },
        "spread": 12.0,
    },
}


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            digest.update(block)
    return digest.hexdigest()


def aim(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def remove_charmorph_handlers():
    for handler in list(bpy.app.handlers.depsgraph_update_post):
        if getattr(handler, "__module__", "").startswith("CharMorph"):
            bpy.app.handlers.depsgraph_update_post.remove(handler)


def resolve_targets():
    root = bpy.data.objects["V206_GUITAR_ROOT"]
    geometry = GuitarGeometry.from_mapping(load_authoritative_mapping())
    normal = root.matrix_world.to_3x3() @ Vector((0.0, 0.0, 1.0))
    normal.normalize()
    targets = {}
    metadata = {}
    for digit, (string_id, fret, contact) in VISIBLE_MAP.items():
        point = geometry.local_pad_from_neutral(string_id, fret, behind_fraction=0.18)
        local = Vector((NEUTRAL_FRET_X + point[0], point[1], CONTACT_Z))
        surface = root.matrix_world @ local
        hover = 0.010 if not contact else 0.0
        target = surface + normal * (PAD_OFFSETS_M[digit] + hover)
        targets[digit] = target
        metadata[digit] = {
            "string": string_id, "fret": fret, "contact": contact,
            "target_world_m": list(target), "surface_world_m": list(surface),
            "hover_clearance_m": hover,
        }
    return targets, metadata


def add_rotation(bone, axis_name, degrees):
    axis = "XYZ".index(axis_name)
    bone.rotation_mode = "XYZ"
    bone.rotation_euler[axis] += math.radians(degrees)


def pose_candidate(settings):
    rig = bpy.data.objects["V310_REOM_RIG"]
    guitar_root = bpy.data.objects["V206_GUITAR_ROOT"]
    hand = rig.pose.bones["hand_ik.L"]
    hand_world = rig.matrix_world @ hand.matrix
    hand_world.translation += Vector(settings["hand_delta"])
    if settings.get("guitar_delta"):
        hand_world.translation += guitar_root.matrix_world.to_3x3() @ Vector(settings["guitar_delta"])
    if settings["hand_roll"]:
        pivot = hand_world.translation.copy()
        hand_world = hand_world @ Matrix.Rotation(math.radians(settings["hand_roll"]), 4, "Y")
        hand_world.translation = pivot
    if settings.get("guitar_yaw"):
        pivot = hand_world.translation.copy()
        axis = guitar_root.matrix_world.to_3x3() @ Vector((0.0, 0.0, 1.0))
        axis.normalize()
        rotation = Matrix.Rotation(math.radians(settings["guitar_yaw"]), 4, axis)
        hand_world = Matrix.Translation(pivot) @ rotation @ Matrix.Translation(-pivot) @ hand_world
    hand.matrix = rig.matrix_world.inverted() @ hand_world
    bpy.context.view_layer.update()

    targets, metadata = resolve_targets()
    for digit in ("index", "middle", "ring", "pinky", "thumb"):
        prefix = f"f_{digit}" if digit != "thumb" else "thumb"
        ik_name = f"f_{digit}.01_ik.L" if digit != "thumb" else "thumb.01_ik.L"
        ik = rig.pose.bones[ik_name]
        ik["FK_IK"] = 0.0
        curl = settings.get("curl_by_digit", {}).get(digit, settings.get("curl", (18.0, 28.0, 16.0)))
        for joint, degrees in enumerate(curl, 1):
            add_rotation(rig.pose.bones[f"{prefix}.{joint:02d}.L"], FLEX_AXES[digit], degrees)
        spread = settings.get("spread_by_digit", {}).get(digit, settings["spread"])
        if spread:
            axis, sign = LATERAL[digit]
            add_rotation(rig.pose.bones[f"{prefix}.01.L"], axis, sign * spread)
    bpy.context.view_layer.update()

    # The FK pose now establishes a human bend plane; terminal IK closes only
    # the residual to the exact string pad centers.
    for digit, target in targets.items():
        control = rig.pose.bones[f"f_{digit}.01_ik.L"]
        control["FK_IK"] = 1.0
        world = rig.matrix_world @ control.matrix
        world.translation = target
        control.matrix = rig.matrix_world.inverted() @ world
    thumb = rig.pose.bones["thumb.01_ik.L"]
    thumb["FK_IK"] = 1.0
    world = rig.matrix_world @ thumb.matrix
    world.translation = THUMB_TARGET
    thumb.matrix = rig.matrix_world.inverted() @ world
    bpy.context.view_layer.update()
    return rig, metadata


def render_candidate(label, settings):
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    remove_charmorph_handlers()
    rig, metadata = pose_candidate(settings)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.look = "AgX - Medium High Contrast"
    camera = bpy.data.objects["V287_GUITAR_CAMERA"]
    camera.location = Vector((0.72, -1.48, 1.49))
    camera.data.lens = 105.0
    aim(camera, Vector((0.26, -0.39, 1.38)))
    scene.camera = camera
    scene.render.resolution_x = 900
    scene.render.resolution_y = 700
    scene.render.resolution_percentage = 100
    path = RENDERS / f"v319_{label}.png"
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    tips = {
        digit: list(rig.matrix_world @ rig.pose.bones[f"DEF-f_{digit}.03.L"].tail)
        for digit in VISIBLE_MAP
    }
    errors = {
        digit: (Vector(tips[digit]) - Vector(metadata[digit]["target_world_m"])).length
        for digit in VISIBLE_MAP
    }
    return {
        "settings": settings,
        "targets": metadata,
        "tips_world_m": tips,
        "tip_target_errors_m": errors,
        "max_tip_target_error_m": max(errors.values()),
        "render": {"path": str(path.relative_to(ROOT)), "sha256": sha(path)},
    }


def main():
    RENDERS.mkdir(parents=True, exist_ok=True)
    AUDIT.mkdir(parents=True, exist_ok=True)
    candidates = {label: render_candidate(label, settings) for label, settings in CANDIDATES.items()}
    record = {
        "schema": "v319-hybrid-fretting-probe-v1",
        "status": "VISUAL_SELECTION_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)},
        "method": "FK curl and spread seed, then position-only Rigify terminal IK to v2 pad targets",
        "mapping_authority": "references/m3/m3_chord_mapping_v2.json visible_pose_targets",
        "candidates": candidates,
    }
    (AUDIT / "v319_hybrid_fretting_probe.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V319_HYBRID_FRETTING_PROBE_OK=" + json.dumps({"candidates": list(candidates), "max_errors": {k: v["max_tip_target_error_m"] for k, v in candidates.items()}}, sort_keys=True))


if __name__ == "__main__":
    main()
