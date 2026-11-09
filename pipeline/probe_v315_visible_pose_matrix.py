"""Probe the authoritative v2 three-contact-plus-hover fretting pose."""

from pathlib import Path
import hashlib
import json
import math
import sys

import bpy
from mathutils import Matrix, Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v310_reom_scene_alignment" / "Character_An_reom_scene_alignment_v310.blend"
STAGE = ROOT / "production_v315_visible_pose_probe"
RENDERS = STAGE / "renders"
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
CANDIDATES = {
    "A_base": (Vector((-0.030, 0.025, 0.005)), 0.0),
    "B_forward": (Vector((-0.020, 0.025, 0.005)), 0.0),
    "C_deeper": (Vector((-0.040, 0.030, 0.000)), 0.0),
    "D_roll_neg10": (Vector((-0.030, 0.025, 0.005)), -10.0),
    "E_roll_pos10": (Vector((-0.030, 0.025, 0.005)), 10.0),
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
        string_surface = root.matrix_world @ local
        hover = 0.010 if not contact else 0.0
        target = string_surface + normal * (PAD_OFFSETS_M[digit] + hover)
        targets[digit] = target
        metadata[digit] = {
            "string": string_id,
            "fret": fret,
            "contact": contact,
            "string_surface_world_m": list(string_surface),
            "finger_tip_center_world_m": list(target),
            "pad_offset_m": PAD_OFFSETS_M[digit],
            "hover_clearance_m": hover,
        }
    return targets, metadata, normal


def pose_candidate(delta, roll_degrees):
    rig = bpy.data.objects["V310_REOM_RIG"]
    hand = rig.pose.bones["hand_ik.L"]
    hand_world = rig.matrix_world @ hand.matrix
    hand_world.translation += delta
    if roll_degrees:
        pivot = hand_world.translation.copy()
        hand_world = hand_world @ Matrix.Rotation(math.radians(roll_degrees), 4, "Y")
        hand_world.translation = pivot
    hand.matrix = rig.matrix_world.inverted() @ hand_world
    bpy.context.view_layer.update()

    targets, metadata, normal = resolve_targets()
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
    return rig, targets, metadata, normal


def render_candidate(label, delta, roll):
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    remove_charmorph_handlers()
    rig, targets, metadata, normal = pose_candidate(delta, roll)
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
    path = RENDERS / f"v315_{label}.png"
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return {
        "delta_m": list(delta),
        "roll_degrees_local_y": roll,
        "surface_normal_world": list(normal),
        "targets": metadata,
        "render": {"path": str(path.relative_to(ROOT)), "sha256": sha(path)},
        "hand_head_world_m": list(rig.matrix_world @ rig.pose.bones["DEF-hand.L"].head),
        "digit_tips_world_m": {
            digit: list(rig.matrix_world @ rig.pose.bones[f"DEF-f_{digit}.03.L"].tail)
            for digit in targets
        },
        "thumb_tip_world_m": list(rig.matrix_world @ rig.pose.bones["DEF-thumb.03.L"].tail),
    }


def main():
    for folder in (STAGE, RENDERS, AUDIT):
        folder.mkdir(parents=True, exist_ok=True)
    records = {label: render_candidate(label, *settings) for label, settings in CANDIDATES.items()}
    record = {
        "schema": "v315-visible-pose-probe-v1",
        "status": "VISUAL_SELECTION_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)},
        "mapping_authority": "references/m3/m3_chord_mapping_v2.json visible_pose_targets",
        "rejected_legacy_map": "index S5/F9 and middle S4/F10 retained only as rejected comparison",
        "candidates": records,
    }
    (AUDIT / "v315_visible_pose_probe.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V315_VISIBLE_POSE_PROBE_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
