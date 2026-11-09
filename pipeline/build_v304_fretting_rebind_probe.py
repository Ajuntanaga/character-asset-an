"""Replace overlapping automatic hand weights with bone-local segment weights."""

from pathlib import Path
import hashlib
import json
import math

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v300_guitar_visual_acceptance" / "Character_An_guitar_visual_acceptance_v300.blend"
STAGE = ROOT / "production_v304_fretting_rebind_probe"
OUTPUT = STAGE / "Character_An_fretting_rebind_probe_v304.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"
HAND = "V248_FRETTING_HAND_REALISTIC"
RIG = "V250_FRETTING_HAND_RIG"


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            digest.update(block)
    return digest.hexdigest()


def segment_distance(point, a, b):
    ab = b - a
    factor = max(0.0, min(1.0, (point - a).dot(ab) / max(ab.length_squared, 1e-12)))
    return (point - a.lerp(b, factor)).length


def point_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def rebind(hand, rig):
    deform_names = ["hand_root"] + [f"{digit}_{joint:02d}" for digit in ("index", "middle", "ring", "pinky", "thumb") for joint in range(1, 4)]
    for group in list(hand.vertex_groups):
        hand.vertex_groups.remove(group)
    groups = {name: hand.vertex_groups.new(name=name) for name in deform_names}
    bones = {name: rig.data.bones[name] for name in deform_names}
    assignments = {name: 0 for name in deform_names}
    entropy = []
    sigma = .013
    for vertex in hand.data.vertices:
        point = vertex.co
        ranked = sorted((segment_distance(point, bone.head_local, bone.tail_local), name) for name, bone in bones.items())
        nearest = ranked[:3]
        raw = [(math.exp(-((distance / sigma) ** 2)), name) for distance, name in nearest]
        total = sum(weight for weight, _name in raw) or 1.0
        normalized = [(weight / total, name) for weight, name in raw if weight / total >= .025]
        renorm = sum(weight for weight, _name in normalized) or 1.0
        normalized = [(weight / renorm, name) for weight, name in normalized]
        for weight, name in normalized:
            groups[name].add([vertex.index], weight, "REPLACE")
            assignments[name] += 1
        entropy.append(len(normalized))
    return {
        "assignment_counts": assignments,
        "max_groups_per_vertex": max(entropy),
        "mean_groups_per_vertex": sum(entropy) / len(entropy),
    }


def render(scene, camera, path):
    camera.location = Vector((.72, -1.48, 1.49))
    camera.data.lens = 105.0
    point_at(camera, Vector((.262, -.397, 1.383)))
    scene.camera = camera
    scene.render.resolution_x = 1200
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(path)}


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    for folder in (STAGE, RENDERS, AUDIT):
        folder.mkdir(parents=True, exist_ok=True)
    hand = bpy.data.objects[HAND]
    rig = bpy.data.objects[RIG]
    scene = bpy.context.scene
    camera = bpy.data.objects["V287_GUITAR_CAMERA"]
    pose = {bone.name: (list(bone.location), list(bone.rotation_euler), list(bone.scale)) for bone in rig.pose.bones}
    bind = rebind(hand, rig)
    bpy.context.view_layer.update()
    renders = {"source_pose": render(scene, camera, RENDERS / "v304_source_pose.png")}

    for bone in rig.pose.bones:
        bone.location = (0.0, 0.0, 0.0)
        bone.rotation_mode = "XYZ"
        bone.rotation_euler = (0.0, 0.0, 0.0)
        bone.scale = (1.0, 1.0, 1.0)
    bpy.context.view_layer.update()
    renders["neutral"] = render(scene, camera, RENDERS / "v304_neutral.png")

    for digit in ("index", "middle", "ring", "pinky"):
        rig.pose.bones[f"{digit}_01"].rotation_euler.x = math.radians(28)
        rig.pose.bones[f"{digit}_02"].rotation_euler.x = math.radians(52)
        rig.pose.bones[f"{digit}_03"].rotation_euler.x = math.radians(34)
    rig.pose.bones["thumb_01"].rotation_euler.x = math.radians(22)
    rig.pose.bones["thumb_02"].rotation_euler.x = math.radians(38)
    rig.pose.bones["thumb_03"].rotation_euler.x = math.radians(24)
    bpy.context.view_layer.update()
    renders["curl_x"] = render(scene, camera, RENDERS / "v304_curl_x.png")

    for bone in rig.pose.bones:
        location, rotation, scale = pose[bone.name]
        bone.location = location
        bone.rotation_euler = rotation
        bone.scale = scale
    bpy.context.view_layer.update()
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v304-fretting-rebind-probe-v1",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)},
        "bind": bind,
        "renders": renders,
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha(OUTPUT)},
        "status": "VISUAL_REVIEW_REQUIRED",
    }
    (AUDIT / "v304_fretting_rebind_probe.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V304_FRETTING_REBIND_PROBE_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
