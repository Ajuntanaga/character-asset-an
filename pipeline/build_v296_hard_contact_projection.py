"""Project V295 finger endpoints back to their exact pre-clearance targets."""

from pathlib import Path
import hashlib
import json

import bpy
from mathutils import Matrix, Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v295_fretting_arc_clearance" / "Character_An_fretting_arc_clearance_v295.blend"
SOURCE_AUDIT = ROOT / "production_v295_fretting_arc_clearance" / "audit" / "v295_fretting_arc_clearance.json"
STAGE = ROOT / "production_v296_hard_contact_projection"
OUTPUT = STAGE / "Character_An_hard_contact_projection_v296.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"
RIG = "V250_FRETTING_HAND_RIG"
HAND = "V248_FRETTING_HAND_REALISTIC"
NECK = "V206_NECK"
DIGITS = ("index", "middle", "ring", "pinky")


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            digest.update(block)
    return digest.hexdigest()


def point_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def tail_world(rig, digit):
    return rig.matrix_world @ rig.pose.bones[f"{digit}_03"].tail


def project_tail(rig, digit, target):
    root = rig.pose.bones[f"{digit}_01"]
    history = []
    epsilon = 0.0001
    for iteration in range(12):
        current = tail_world(rig, digit)
        error = target - current
        history.append(float(error.length))
        if error.length < 0.00005:
            break
        base = root.location.copy()
        columns = []
        for axis in range(3):
            root.location = base.copy()
            root.location[axis] += epsilon
            bpy.context.view_layer.update()
            columns.append((tail_world(rig, digit) - current) / epsilon)
        root.location = base
        bpy.context.view_layer.update()
        jacobian = Matrix((columns[0], columns[1], columns[2])).transposed()
        try:
            delta = jacobian.inverted() @ error
        except ValueError:
            delta = error
        if delta.length > .025:
            delta.normalize()
            delta *= .025
        root.location += delta
        bpy.context.view_layer.update()
    final = tail_world(rig, digit)
    return {
        "iterations": len(history),
        "error_history_m": history,
        "target_world": [float(v) for v in target],
        "final_world": [float(v) for v in final],
        "final_error_m": float((final - target).length),
        "root_location": [float(v) for v in root.location],
    }


def neck_samples(rig, neck, digit):
    result = []
    for joint in range(1, 4):
        bone = rig.pose.bones[f"{digit}_{joint:02d}"]
        head = rig.matrix_world @ bone.head
        tail = rig.matrix_world @ bone.tail
        for point in (head, head.lerp(tail, .33), head.lerp(tail, .66), tail):
            local = neck.matrix_world.inverted() @ point
            inside = -0.035 < local.x < .610 and abs(local.y) < .055 and -.035 < local.z < .016
            result.append({"local": [round(float(v), 6) for v in local], "inside": inside})
    return {"inside_samples": sum(item["inside"] for item in result), "samples": result}


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
    source_record = json.loads(SOURCE_AUDIT.read_text())
    rig = bpy.data.objects[RIG]
    neck = bpy.data.objects[NECK]
    projections = {}
    for digit in DIGITS:
        target = Vector(source_record["solves"][digit]["target_tail_world"])
        projections[digit] = project_tail(rig, digit, target)
        projections[digit]["clearance"] = neck_samples(rig, neck, digit)
    hand = bpy.data.objects[HAND]
    hand.data.materials.clear()
    hand.data.materials.append(bpy.data.materials["MAT_V211_NEUTRAL_CLAY"])
    bpy.context.view_layer.update()

    scene = bpy.context.scene
    camera = bpy.data.objects["V287_GUITAR_CAMERA"]
    center = neck.matrix_world @ Vector((.33, 0.0, -.005))
    player_a = center + neck.matrix_world.to_3x3() @ Vector((0.0, -.48, -.42))
    player_b = center + neck.matrix_world.to_3x3() @ Vector((-.10, .42, -.52))
    views = {
        "full": (Vector((0.0, -3.75, 1.02)), Vector((0.0, -0.02, 1.0)), 66.0, (900, 1000)),
        "contact_front": (Vector((0.72, -1.48, 1.49)), Vector((0.27, -0.39, 1.39)), 105.0, (1200, 900)),
        "player_a": (player_a, center, 96.0, (1200, 900)),
        "player_b": (player_b, center, 96.0, (1200, 900)),
    }
    renders = {}
    for label, (location, target, lens, resolution) in views.items():
        camera.location = location
        camera.data.lens = lens
        point_at(camera, target)
        renders[label] = render(scene, camera, RENDERS / f"v296_{label}.png", resolution)
    scene["V296_STATUS"] = "HARD_CONTACT_PROJECTION_VISUAL_REVIEW_REQUIRED"
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v296-hard-contact-projection-v1",
        "status": "VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)},
        "projections": projections,
        "renders": renders,
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha(OUTPUT)},
    }
    (AUDIT / "v296_hard_contact_projection.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V296_HARD_CONTACT_PROJECTION_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
