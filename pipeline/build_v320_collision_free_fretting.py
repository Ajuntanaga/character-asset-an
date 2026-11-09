"""Build the collision-audited guitar-space fretting-hand solution."""

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


SOURCE = ROOT / "production_v318_reference_guitar_rebuild" / "Character_An_reference_guitar_rebuild_v318.blend"
STAGE = ROOT / "production_v320_collision_free_fretting"
OUTPUT = STAGE / "Character_An_collision_free_fretting_v320.blend"
RENDERS = STAGE / "renders" / "selected"
AUDIT = STAGE / "audit"
SETTINGS = {
    "hand_delta": (-0.030, 0.025, 0.005),
    "hand_roll": 0.0,
    "guitar_yaw": -40.0,
    "guitar_delta": (-0.045, 0.005, 0.0),
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


def render(scene, camera, path, location, target, lens, resolution):
    camera.location = location
    camera.data.lens = lens
    aim(camera, target)
    scene.camera = camera
    scene.render.resolution_x, scene.render.resolution_y = resolution
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(path)}


def board_half_width(x):
    fraction = max(0.0, min(1.0, (x + 0.022) / (0.563 + 0.022)))
    return 0.0310 + fraction * (0.0445 - 0.0310)


def collision_proxy(rig, guitar_root):
    inverse = guitar_root.matrix_world.inverted()
    proxy_radius = 0.0045
    records = {}
    flagged = []
    for digit in ("index", "middle", "ring", "pinky"):
        records[digit] = []
        for joint in range(1, 4):
            bone = rig.pose.bones[f"DEF-f_{digit}.{joint:02d}.L"]
            head = inverse @ (rig.matrix_world @ bone.head)
            tail = inverse @ (rig.matrix_world @ bone.tail)
            samples = []
            for sample_index in range(21):
                t = sample_index / 20.0
                point = head.lerp(tail, t)
                half_width = board_half_width(point.x)
                lateral_clearance = abs(point.y) - half_width
                top_clearance = point.z - 0.0155
                inside_longitudinal = -0.022 <= point.x <= 0.563
                risk = bool(
                    inside_longitudinal
                    and lateral_clearance < proxy_radius
                    and top_clearance < proxy_radius
                    and point.z > -0.0315
                )
                if risk:
                    flagged.append({"digit": digit, "bone": bone.name, "sample": sample_index})
                samples.append({
                    "t": t,
                    "guitar_local_m": list(point),
                    "lateral_clearance_m": lateral_clearance,
                    "top_clearance_m": top_clearance,
                    "risk": risk,
                })
            records[digit].append({"bone": bone.name, "samples": samples})
    return {
        "proxy_radius_m": proxy_radius,
        "method": "21 centerline samples per phalanx against fretboard expanded by a 4.5 mm conservative finger radius",
        "flagged_sample_count": len(flagged),
        "flagged_samples": flagged,
        "digits": records,
    }


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    pose.remove_charmorph_handlers()
    for folder in (STAGE, RENDERS, AUDIT):
        folder.mkdir(parents=True, exist_ok=True)
    rig, targets = pose.pose_candidate(SETTINGS)
    guitar_root = bpy.data.objects["V206_GUITAR_ROOT"]
    target_center = sum((Vector(entry["target_world_m"]) for entry in targets.values()), Vector()) / len(targets)
    center_local = guitar_root.matrix_world.inverted() @ target_center
    collision = collision_proxy(rig, guitar_root)

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.look = "AgX - Medium High Contrast"
    camera = bpy.data.objects["V287_GUITAR_CAMERA"]
    renders = {
        "front": render(scene, camera, RENDERS / "v320_front.png", Vector((0.72, -1.48, 1.49)), target_center, 105.0, (950, 760)),
        "string_plane": render(
            scene, camera, RENDERS / "v320_string_plane.png",
            guitar_root.matrix_world @ (center_local + Vector((0.0, 0.48, 0.09))), target_center, 96.0, (950, 760),
        ),
        "rear_neck": render(
            scene, camera, RENDERS / "v320_rear_neck.png",
            guitar_root.matrix_world @ (center_local + Vector((0.0, 0.0, -0.58))), target_center, 100.0, (950, 760),
        ),
        "treble_oblique": render(
            scene, camera, RENDERS / "v320_treble_oblique.png",
            guitar_root.matrix_world @ (center_local + Vector((-0.12, -0.40, 0.42))), target_center, 102.0, (950, 760),
        ),
        "full_character": render(
            scene, camera, RENDERS / "v320_full_character.png",
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
    inverse = guitar_root.matrix_world.inverted()
    mcp_bases = {
        digit: list(inverse @ (rig.matrix_world @ rig.pose.bones[f"DEF-f_{digit}.01.L"].head))
        for digit in targets
    }
    scene["V320_STATUS"] = "GUITAR_SPACE_WRIST_YAW_FRETTING_MULTI_VIEW_REVIEW_REQUIRED"
    scene["V320_COLLISION_PROXY_FLAGS"] = collision["flagged_sample_count"]
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v320-collision-free-fretting-v1",
        "status": "BUILT_MULTI_VIEW_AND_COLLISION_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)},
        "settings": SETTINGS,
        "mapping_authority": "references/m3/m3_chord_mapping_v2.json visible_pose_targets",
        "targets": targets,
        "tip_target_errors_m": errors,
        "max_tip_target_error_m": max(errors.values()),
        "mcp_bases_guitar_local_m": mcp_bases,
        "minimum_mcp_lateral_y_m": min(value[1] for value in mcp_bases.values()),
        "fretboard_half_width_near_contacts_m": 0.039,
        "collision_proxy": collision,
        "renders": renders,
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha(OUTPUT)},
    }
    (AUDIT / "v320_collision_free_fretting.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V320_COLLISION_FREE_FRETTING_OK=" + json.dumps({
        "max_error_m": max(errors.values()),
        "minimum_mcp_y_m": min(value[1] for value in mcp_bases.values()),
        "collision_proxy_flags": collision["flagged_sample_count"],
        "output_sha256": sha(OUTPUT),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
