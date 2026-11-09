"""Probe lower wrist height and hand-axis roll for a readable fretting arch."""

from pathlib import Path
import hashlib
import json
import math

import bpy
from mathutils import Matrix, Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v310_reom_scene_alignment" / "Character_An_reom_scene_alignment_v310.blend"
STAGE = ROOT / "production_v314_reom_wrist_roll_probe"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"
CONTACTS = {
    "index": Vector((0.2671270, -0.4045161, 1.3946022)),
    "middle": Vector((0.2444796, -0.4026991, 1.3896780)),
    "ring": Vector((0.2757289, -0.4060766, 1.3818460)),
    "pinky": Vector((0.2460079, -0.4042325, 1.3534319)),
}
THUMB = Vector((0.2470, -0.3150, 1.3720))
CANDIDATES = {
    "A_low_roll_neg": (Vector((-0.030, 0.025, -0.020)), -30.0),
    "B_lower_roll_neg": (Vector((-0.030, 0.025, -0.040)), -30.0),
    "C_low_roll_pos": (Vector((-0.030, 0.025, -0.020)), 30.0),
    "D_lower_roll_pos": (Vector((-0.030, 0.025, -0.040)), 30.0),
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


def pose_candidate(delta, roll_degrees):
    rig = bpy.data.objects["V310_REOM_RIG"]
    hand = rig.pose.bones["hand_ik.L"]
    hand_world = rig.matrix_world @ hand.matrix
    hand_world.translation += delta
    pivot = hand_world.translation.copy()
    hand_world = hand_world @ Matrix.Rotation(math.radians(roll_degrees), 4, "Y")
    hand_world.translation = pivot
    hand.matrix = rig.matrix_world.inverted() @ hand_world
    bpy.context.view_layer.update()
    for digit, target in CONTACTS.items():
        control = rig.pose.bones[f"f_{digit}.01_ik.L"]
        control["FK_IK"] = 1.0
        world = rig.matrix_world @ control.matrix
        world.translation = target
        control.matrix = rig.matrix_world.inverted() @ world
    thumb = rig.pose.bones["thumb.01_ik.L"]
    thumb["FK_IK"] = 1.0
    world = rig.matrix_world @ thumb.matrix
    world.translation = THUMB
    thumb.matrix = rig.matrix_world.inverted() @ world
    bpy.context.view_layer.update()
    return rig


def render_candidate(label, delta, roll):
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    remove_charmorph_handlers()
    rig = pose_candidate(delta, roll)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.look = "AgX - Medium High Contrast"
    camera = bpy.data.objects["V287_GUITAR_CAMERA"]
    camera.location = Vector((0.72, -1.48, 1.49))
    camera.data.lens = 105.0
    aim(camera, Vector((0.26, -0.39, 1.39)))
    scene.camera = camera
    scene.render.resolution_x = 900
    scene.render.resolution_y = 700
    scene.render.resolution_percentage = 100
    path = RENDERS / f"v314_{label}.png"
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return {
        "delta_m": list(delta),
        "roll_degrees_local_y": roll,
        "render": {"path": str(path.relative_to(ROOT)), "sha256": sha(path)},
        "hand_head_world_m": list(rig.matrix_world @ rig.pose.bones["DEF-hand.L"].head),
    }


def main():
    for folder in (STAGE, RENDERS, AUDIT):
        folder.mkdir(parents=True, exist_ok=True)
    records = {label: render_candidate(label, *settings) for label, settings in CANDIDATES.items()}
    record = {
        "schema": "v314-reom-wrist-roll-probe-v1",
        "status": "VISUAL_SELECTION_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)},
        "candidates": records,
    }
    (AUDIT / "v314_reom_wrist_roll_probe.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V314_REOM_WRIST_ROLL_PROBE_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
