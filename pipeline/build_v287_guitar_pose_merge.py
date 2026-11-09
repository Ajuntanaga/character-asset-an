"""Merge accepted guitar into V286 and apply the repaired upper-body guitar pose."""

from pathlib import Path
import hashlib
import json

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v286_clean_baseline" / "Character_An_clean_baseline_v286.blend"
GUITAR_SOURCE = ROOT / "production_v236_guitar_body_anchor_fit" / "Character_An_guitar_body_anchor_v236.blend"
STAGE = ROOT / "production_v287_guitar_pose_merge"
OUTPUT = STAGE / "Character_An_guitar_pose_merge_v287.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"
RIG = "V239_CLEAN_CHARACTER_RIG"
COLLECTION = "V206_GUITAR_REBUILD"
GUITAR_ROOT = "V206_GUITAR_ROOT"


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            digest.update(block)
    return digest.hexdigest()


def point_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def direction_matrix(location, direction):
    matrix = direction.normalized().to_track_quat("Y", "Z").to_matrix().to_4x4()
    matrix.translation = location
    return matrix


def set_world_matrix(rig, bone_name, matrix):
    rig.pose.bones[bone_name].matrix = rig.matrix_world.inverted() @ matrix


def append_guitar():
    with bpy.data.libraries.load(str(GUITAR_SOURCE), link=False) as (source, target):
        if COLLECTION not in source.collections:
            raise RuntimeError(f"Missing {COLLECTION}")
        target.collections = [COLLECTION]
    collection = target.collections[0]
    bpy.context.scene.collection.children.link(collection)
    for name in ("V206_KEY", "V206_FILL", "V206_RIM"):
        obj = bpy.data.objects.get(name)
        if obj:
            obj.hide_render = True
            obj.hide_viewport = True
    return collection


def render(scene, camera, path, resolution):
    scene.camera = camera
    scene.render.resolution_x, scene.render.resolution_y = resolution
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(path)}


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    for folder in (STAGE, RENDERS, AUDIT):
        folder.mkdir(parents=True, exist_ok=True)
    collection = append_guitar()
    root = bpy.data.objects[GUITAR_ROOT]
    root["v287_transform_authority"] = "V236_ACCEPTED_BODY_ANCHOR"
    root["v287_contact_status"] = "NOT_YET_SOLVED"
    rig = bpy.data.objects[RIG]
    pose_data = {
        "L": (Vector((0.195, -0.345, 1.340)), Vector((0.53, 0.04, 1.245)), Vector((0.060, -0.045, 0.030))),
        "R": (Vector((-0.145, -0.345, 1.260)), Vector((-0.50, 0.04, 1.185)), Vector((0.070, -0.040, -0.060))),
    }
    for side, (hand_location, pole_location, hand_direction) in pose_data.items():
        set_world_matrix(rig, f"hand_ik.{side}", direction_matrix(hand_location, hand_direction))
        pole = rig.matrix_world @ rig.pose.bones[f"upper_arm_ik_target.{side}"].matrix
        pole.translation = pole_location
        set_world_matrix(rig, f"upper_arm_ik_target.{side}", pole)
    bpy.context.view_layer.update()

    scene = bpy.context.scene
    camera = bpy.data.objects["V286_FULL_CAMERA"]
    camera.name = "V287_GUITAR_CAMERA"
    views = {
        "front": (Vector((0.0, -3.75, 1.02)), Vector((0.0, -0.02, .99)), 66.0, (900, 1000)),
        "three_quarter": (Vector((-2.55, -2.75, 1.14)), Vector((0.0, -0.03, 1.02)), 70.0, (900, 1000)),
        "instrument": (Vector((-1.38, -2.20, 1.16)), Vector((0.0, -0.12, 1.20)), 78.0, (1100, 850)),
    }
    renders = {}
    for label, (location, target, lens, resolution) in views.items():
        camera.location = location
        camera.data.lens = lens
        point_at(camera, target)
        renders[label] = render(scene, camera, RENDERS / f"v287_{label}.png", resolution)
    scene["V287_STATUS"] = "GUITAR_MERGED_CONTACT_UNSOLVED"
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v287-guitar-pose-merge-v1",
        "status": "GUITAR_MERGED_CONTACT_UNSOLVED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)},
        "guitar_source": {"path": str(GUITAR_SOURCE.relative_to(ROOT)), "sha256": sha(GUITAR_SOURCE)},
        "guitar": {"collection": COLLECTION, "object_count": len(collection.all_objects), "root": GUITAR_ROOT},
        "pose_authority": "V277C_FRAME_70_REPAIRED_WORLD_MATRIX_IK",
        "renders": renders,
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha(OUTPUT)},
    }
    (AUDIT / "v287_guitar_pose_merge.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V287_GUITAR_POSE_MERGE_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
