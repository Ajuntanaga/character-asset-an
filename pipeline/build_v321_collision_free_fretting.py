"""Promote the zero-flag visible-pose fretting-hand solution."""

from pathlib import Path
import hashlib
import importlib
import json
import sys

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline import probe_v319_hybrid_fretting_matrix as pose
pose = importlib.reload(pose)
from pipeline import build_v320_collision_free_fretting as v320
v320 = importlib.reload(v320)


SOURCE = ROOT / "production_v318_reference_guitar_rebuild" / "Character_An_reference_guitar_rebuild_v318.blend"
STAGE = ROOT / "production_v321_collision_free_fretting"
OUTPUT = STAGE / "Character_An_collision_free_fretting_v321.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"
SETTINGS = {
    "hand_delta": (-0.030, 0.025, 0.005),
    "hand_roll": 0.0,
    "guitar_yaw": -40.0,
    "guitar_delta": (-0.055, 0.010, 0.0),
    "curl": (14.0, 24.0, 14.0),
    "spread": 8.0,
}


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    pose.remove_charmorph_handlers()
    for folder in (STAGE, RENDERS, AUDIT):
        folder.mkdir(parents=True, exist_ok=True)
    rig, targets = pose.pose_candidate(SETTINGS)
    root = bpy.data.objects["V206_GUITAR_ROOT"]
    collision = v320.collision_proxy(rig, root)
    if collision["flagged_sample_count"]:
        raise RuntimeError(f"Selected V321 solution has {collision['flagged_sample_count']} collision proxy flags")

    target_center = sum((Vector(entry["target_world_m"]) for entry in targets.values()), Vector()) / len(targets)
    center_local = root.matrix_world.inverted() @ target_center
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.look = "AgX - Medium High Contrast"
    camera = bpy.data.objects["V287_GUITAR_CAMERA"]
    renders = {
        "front": v320.render(scene, camera, RENDERS / "v321_front.png", Vector((0.72, -1.48, 1.49)), target_center, 105.0, (950, 760)),
        "string_plane": v320.render(
            scene, camera, RENDERS / "v321_string_plane.png",
            root.matrix_world @ (center_local + Vector((0.0, 0.48, 0.09))), target_center, 96.0, (950, 760),
        ),
        "rear_neck": v320.render(
            scene, camera, RENDERS / "v321_rear_neck.png",
            root.matrix_world @ (center_local + Vector((0.0, 0.0, -0.58))), target_center, 100.0, (950, 760),
        ),
        "treble_oblique": v320.render(
            scene, camera, RENDERS / "v321_treble_oblique.png",
            root.matrix_world @ (center_local + Vector((-0.12, -0.40, 0.42))), target_center, 102.0, (950, 760),
        ),
        "full_character": v320.render(
            scene, camera, RENDERS / "v321_full_character.png",
            Vector((0.0, -3.75, 1.02)), Vector((0.0, -0.02, 1.0)), 66.0, (900, 1000),
        ),
    }
    tips = {
        digit: rig.matrix_world @ rig.pose.bones[f"DEF-f_{digit}.03.L"].tail
        for digit in targets
    }
    errors = {
        digit: (tips[digit] - Vector(targets[digit]["target_world_m"])).length
        for digit in targets
    }
    inverse = root.matrix_world.inverted()
    bases = {
        digit: list(inverse @ (rig.matrix_world @ rig.pose.bones[f"DEF-f_{digit}.01.L"].head))
        for digit in targets
    }
    scene["V321_STATUS"] = "ZERO_PROXY_COLLISION_V2_FRETTING_HAND_VISUAL_REVIEW_REQUIRED"
    scene["V321_COLLISION_PROXY_FLAGS"] = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v321-collision-free-fretting-v1",
        "status": "ZERO_PROXY_FLAGS_MULTI_VIEW_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)},
        "settings": SETTINGS,
        "mapping_authority": "references/m3/m3_chord_mapping_v2.json visible_pose_targets",
        "targets": targets,
        "tip_target_errors_m": errors,
        "max_tip_target_error_m": max(errors.values()),
        "mcp_bases_guitar_local_m": bases,
        "minimum_mcp_lateral_y_m": min(value[1] for value in bases.values()),
        "collision_proxy": collision,
        "renders": renders,
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha(OUTPUT)},
    }
    (AUDIT / "v321_collision_free_fretting.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V321_COLLISION_FREE_FRETTING_OK=" + json.dumps({
        "max_error_m": max(errors.values()),
        "collision_proxy_flags": collision["flagged_sample_count"],
        "minimum_mcp_y_m": min(value[1] for value in bases.values()),
        "output_sha256": sha(OUTPUT),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
