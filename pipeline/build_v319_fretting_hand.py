"""Build and inspect the selected FK-seeded visible-pose fretting hand."""

from pathlib import Path
import hashlib
import json
import sys

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline import probe_v319_hybrid_fretting_matrix as pose


SOURCE = ROOT / "production_v318_reference_guitar_rebuild" / "Character_An_reference_guitar_rebuild_v318.blend"
STAGE = ROOT / "production_v319_fretting_hand"
OUTPUT = STAGE / "Character_An_fretting_hand_v319.blend"
RENDERS = STAGE / "renders" / "selected"
AUDIT = STAGE / "audit"
SETTINGS = {
    "hand_delta": (-0.030, 0.025, 0.005),
    "hand_roll": 0.0,
    "curl": (14.0, 24.0, 14.0),
    "spread": 8.0,
}


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            digest.update(block)
    return digest.hexdigest()


def aim(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(scene, camera, path, location, target, lens=100.0):
    camera.location = location
    camera.data.lens = lens
    aim(camera, target)
    scene.camera = camera
    scene.render.resolution_x = 950
    scene.render.resolution_y = 760
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(path)}


def joint_clearance(rig, guitar_root):
    inverse = guitar_root.matrix_world.inverted()
    result = {}
    for digit in ("index", "middle", "ring", "pinky", "thumb"):
        prefix = f"DEF-f_{digit}" if digit != "thumb" else "DEF-thumb"
        joints = []
        for joint in range(1, 4):
            bone = rig.pose.bones[f"{prefix}.{joint:02d}.L"]
            head = inverse @ (rig.matrix_world @ bone.head)
            tail = inverse @ (rig.matrix_world @ bone.tail)
            joints.append({
                "bone": bone.name,
                "head_guitar_local_m": list(head),
                "tail_guitar_local_m": list(tail),
            })
        result[digit] = joints
    return result


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    pose.remove_charmorph_handlers()
    for folder in (STAGE, RENDERS, AUDIT):
        folder.mkdir(parents=True, exist_ok=True)
    rig, targets = pose.pose_candidate(SETTINGS)
    guitar_root = bpy.data.objects["V206_GUITAR_ROOT"]
    target_center = sum((Vector(entry["target_world_m"]) for entry in targets.values()), Vector()) / len(targets)
    center_local = guitar_root.matrix_world.inverted() @ target_center

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.look = "AgX - Medium High Contrast"
    camera = bpy.data.objects["V287_GUITAR_CAMERA"]
    renders = {
        "front": render(scene, camera, RENDERS / "v319_front.png", Vector((0.72, -1.48, 1.49)), target_center, 105.0),
        "string_plane": render(
            scene, camera, RENDERS / "v319_string_plane.png",
            guitar_root.matrix_world @ (center_local + Vector((0.00, 0.48, 0.09))), target_center, 96.0,
        ),
        "rear_neck": render(
            scene, camera, RENDERS / "v319_rear_neck.png",
            guitar_root.matrix_world @ (center_local + Vector((0.00, 0.00, -0.58))), target_center, 100.0,
        ),
        "treble_oblique": render(
            scene, camera, RENDERS / "v319_treble_oblique.png",
            guitar_root.matrix_world @ (center_local + Vector((-0.12, -0.40, 0.42))), target_center, 102.0,
        ),
    }

    actual_tips = {
        digit: rig.matrix_world @ rig.pose.bones[f"DEF-f_{digit}.03.L"].tail
        for digit in targets
    }
    errors = {
        digit: (actual_tips[digit] - Vector(targets[digit]["target_world_m"])).length
        for digit in targets
    }
    clearances = joint_clearance(rig, guitar_root)
    scene["V319_STATUS"] = "FK_SEEDED_V2_FRETTING_HAND_VISUAL_REVIEW_REQUIRED"
    scene["V319_MAPPING"] = "index S6/F11 contact; middle S6/F10 hover; ring S7/F9 contact; pinky S8/F11 contact"
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v319-fretting-hand-v1",
        "status": "BUILT_MULTI_VIEW_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)},
        "settings": SETTINGS,
        "mapping_authority": "references/m3/m3_chord_mapping_v2.json visible_pose_targets",
        "targets": targets,
        "tip_target_errors_m": errors,
        "max_tip_target_error_m": max(errors.values()),
        "joint_clearance_guitar_local": clearances,
        "fretboard_top_z_m": 0.0155,
        "string_surface_z_m": 0.02045,
        "renders": renders,
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha(OUTPUT)},
    }
    (AUDIT / "v319_fretting_hand.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V319_FRETTING_HAND_OK=" + json.dumps({"max_error_m": max(errors.values()), "output_sha256": sha(OUTPUT), "renders": renders}, sort_keys=True))


if __name__ == "__main__":
    main()
