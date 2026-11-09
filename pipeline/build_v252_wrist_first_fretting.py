"""Fit the whole wrist to V237 before applying bounded finger articulation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v250_dedicated_hand_rig" / "Character_An_dedicated_hand_rig_v250.blend"
STAGE = ROOT / "production_v252_wrist_first_fretting"
OUTPUT = STAGE / "Character_An_wrist_first_fretting_v252.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"
MAIN_RIG = "V239_CLEAN_CHARACTER_RIG"
ARMATURE = "V250_FRETTING_HAND_RIG"
HAND = "V248_FRETTING_HAND_REALISTIC"
WRIST_DELTA = Vector((-0.0543659, 0.06651615, -0.04731738))
CONTACTS = {
    "index": {"vertex": 233, "string": "S5", "fret": 9, "target": Vector((0.2671270, -0.4045161, 1.3946022))},
    "middle": {"vertex": 213, "string": "S4", "fret": 10, "target": Vector((0.2444796, -0.4026991, 1.3896780))},
    "ring": {"vertex": 13, "string": "S7", "fret": 9, "target": Vector((0.2757289, -0.4060766, 1.3818460))},
    "pinky": {"vertex": 1, "string": "S8", "fret": 11, "target": Vector((0.2460079, -0.4042325, 1.3534319))},
}
THUMB_SURFACE_TARGET = Vector((0.247, -0.315, 1.372))
THUMB_BONE_TARGET = Vector((0.2494, -0.2845, 1.3654))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def point_at(obj: bpy.types.Object, target: Vector) -> None:
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def surface_world(hand: bpy.types.Object, vertex_index: int) -> Vector:
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = hand.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    try:
        return evaluated.matrix_world @ mesh.vertices[vertex_index].co
    finally:
        evaluated.to_mesh_clear()


def solve(armature: bpy.types.Object, hand: bpy.types.Object, digit: str, target: Vector, vertex: int) -> dict:
    bones = [armature.pose.bones[f"{digit}_{joint:02d}"] for joint in range(1, 4)]
    for bone in bones:
        bone.rotation_mode = "XYZ"
        bone.rotation_euler = (0.0, 0.0, 0.0)
    initial = (0.08, 0.0, 0.0, 0.42, 0.28)
    parameters = [
        (bones[0], 0, -0.30, 0.72),
        (bones[0], 1, -0.58, 0.58),
        (bones[0], 2, -0.58, 0.58),
        (bones[1], 0, 0.00, 1.12),
        (bones[2], 0, 0.00, 0.82),
    ]
    if digit == "thumb":
        initial = (0.06, 0.0, 0.0, 0.36, 0.24)
        parameters[0] = (bones[0], 0, -0.38, 0.80)
        parameters[1] = (bones[0], 1, -0.72, 0.72)
        parameters[2] = (bones[0], 2, -0.72, 0.72)
    for (bone, axis, _lower, _upper), value in zip(parameters, initial):
        bone.rotation_euler[axis] = value
    bpy.context.view_layer.update()

    def tip() -> Vector:
        return armature.matrix_world @ bones[-1].tail

    best = (tip() - target).length_squared
    evaluations = 1
    for step in (0.30, 0.16, 0.085, 0.044, 0.022, 0.011, 0.0055, 0.0028):
        for _ in range(4):
            improved = False
            for bone, axis, lower, upper in parameters:
                base = float(bone.rotation_euler[axis])
                local_value = base
                local_cost = best
                for candidate in (base - step, base + step):
                    if candidate < lower or candidate > upper:
                        continue
                    bone.rotation_euler[axis] = candidate
                    bpy.context.view_layer.update()
                    cost = (tip() - target).length_squared
                    evaluations += 1
                    if cost < local_cost:
                        local_cost = cost
                        local_value = candidate
                bone.rotation_euler[axis] = local_value
                bpy.context.view_layer.update()
                if local_cost + 1e-14 < best:
                    best = local_cost
                    improved = True
            if not improved:
                break
    bone_tip = tip()
    surface = surface_world(hand, vertex)
    for bone in bones:
        bone.keyframe_insert(data_path="rotation_euler", frame=1, group=bone.name)
    return {
        "surface_vertex": vertex,
        "bone_target_world_m": [round(float(value), 7) for value in target],
        "bone_tip_world_m": [round(float(value), 7) for value in bone_tip],
        "surface_world_m": [round(float(value), 7) for value in surface],
        "bone_error_m": round((bone_tip - target).length, 7),
        "evaluations": evaluations,
        "rotations_xyz_rad": {bone.name: [round(float(value), 6) for value in bone.rotation_euler] for bone in bones},
    }


def main() -> None:
    if Path(bpy.data.filepath).resolve() != SOURCE.resolve():
        raise RuntimeError(f"Open V250 first: {SOURCE}")
    STAGE.mkdir(parents=True, exist_ok=True)
    RENDERS.mkdir(parents=True, exist_ok=True)
    AUDIT.mkdir(parents=True, exist_ok=True)
    main_rig = bpy.data.objects[MAIN_RIG]
    armature = bpy.data.objects[ARMATURE]
    hand = bpy.data.objects[HAND]
    bpy.context.scene.frame_set(1)
    hand_ik = main_rig.pose.bones["hand_ik.L"]
    world = main_rig.matrix_world @ hand_ik.matrix
    world.translation += WRIST_DELTA
    hand_ik.matrix = main_rig.matrix_world.inverted() @ world
    hand_ik.keyframe_insert(data_path="location", frame=1, group=hand_ik.name)
    if hand_ik.rotation_mode == "QUATERNION":
        hand_ik.keyframe_insert(data_path="rotation_quaternion", frame=1, group=hand_ik.name)
    else:
        hand_ik.keyframe_insert(data_path="rotation_euler", frame=1, group=hand_ik.name)
    bpy.context.view_layer.update()

    solves = {}
    for digit, contact in CONTACTS.items():
        result = solve(armature, hand, digit, contact["target"], contact["vertex"])
        surface = Vector(result["surface_world_m"])
        result.update({
            "string": contact["string"], "fret": contact["fret"],
            "depression_m": 0.00185, "pad_fraction_behind_fret": 0.18,
            "surface_target_world_m": [round(float(value), 7) for value in contact["target"]],
            "surface_error_m": round((surface - contact["target"]).length, 7),
        })
        solves[digit] = result
    thumb = solve(armature, hand, "thumb", THUMB_BONE_TARGET, 695)
    thumb_surface = Vector(thumb["surface_world_m"])
    thumb["surface_target_world_m"] = [round(float(value), 7) for value in THUMB_SURFACE_TARGET]
    thumb["surface_error_m"] = round((thumb_surface - THUMB_SURFACE_TARGET).length, 7)
    thumb["constraint"] = "behind neck"

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.look = "AgX - Medium High Contrast"
    camera = bpy.data.objects["CAM_V211_FRONT"]
    camera.data.type = "PERSP"
    views = {
        "full_front": (Vector((0.0, -3.75, 1.00)), Vector((0.0, 0.0, 1.00)), 66.0, (900, 1000)),
        "contact_front": (Vector((0.72, -1.48, 1.49)), Vector((0.27, -0.39, 1.39)), 105.0, (1200, 900)),
        "contact_oblique": (Vector((0.86, -1.08, 1.25)), Vector((0.27, -0.39, 1.39)), 95.0, (1200, 900)),
    }
    render_records = {}
    for label, (location, target, lens, resolution) in views.items():
        camera.location = location
        camera.data.lens = lens
        point_at(camera, target)
        scene.camera = camera
        scene.render.resolution_x, scene.render.resolution_y = resolution
        scene.render.resolution_percentage = 100
        path = RENDERS / f"v252_{label}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        render_records[label] = {"path": str(path.relative_to(ROOT)), "sha256": sha256(path)}

    scene["V252_STATUS"] = "WRIST_FIRST_BOUNDED_FRETTING_VISUAL_REVIEW_REQUIRED"
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v252-wrist-first-fretting-v1",
        "status": "BUILT_VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha256(SOURCE)},
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha256(OUTPUT)},
        "wrist_delta_m": [round(float(value), 7) for value in WRIST_DELTA],
        "solves": solves,
        "thumb": thumb,
        "max_surface_error_m": max(value["surface_error_m"] for value in solves.values()),
        "renders": render_records,
    }
    (AUDIT / "v252_wrist_first_fretting.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("V252_WRIST_FIRST_FRETTING_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
