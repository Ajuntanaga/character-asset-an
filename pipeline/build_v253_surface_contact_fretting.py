"""Solve V237 fretting contacts against evaluated skin vertices, not bone tips."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v250_dedicated_hand_rig" / "Character_An_dedicated_hand_rig_v250.blend"
STAGE = ROOT / "production_v253_surface_contact_fretting"
OUTPUT = STAGE / "Character_An_surface_contact_fretting_v253.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"
MAIN_RIG = "V239_CLEAN_CHARACTER_RIG"
ARMATURE = "V250_FRETTING_HAND_RIG"
HAND = "V248_FRETTING_HAND_REALISTIC"
WRIST_DELTA = Vector((-0.0543659, 0.06651615, -0.04731738))
CONTACTS = {
    "index": (233, Vector((0.2671270, -0.4045161, 1.3946022)), "S5", 9),
    "middle": (213, Vector((0.2444796, -0.4026991, 1.3896780)), "S4", 10),
    "ring": (13, Vector((0.2757289, -0.4060766, 1.3818460)), "S7", 9),
    "pinky": (1, Vector((0.2460079, -0.4042325, 1.3534319)), "S8", 11),
}
THUMB = (695, Vector((0.247, -0.315, 1.372)))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def point_at(obj, target: Vector) -> None:
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def surface_world(hand, vertex_index: int) -> Vector:
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = hand.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    try:
        return evaluated.matrix_world @ mesh.vertices[vertex_index].co
    finally:
        evaluated.to_mesh_clear()


def solve_surface(armature, hand, digit: str, vertex: int, target: Vector) -> dict:
    bones = [armature.pose.bones[f"{digit}_{joint:02d}"] for joint in range(1, 4)]
    for bone in bones:
        bone.rotation_mode = "XYZ"
        bone.rotation_euler = (0.0, 0.0, 0.0)
    parameters = [
        (bones[0], 0, -0.32, 0.78),
        (bones[0], 1, -0.62, 0.62),
        (bones[0], 2, -0.62, 0.62),
        (bones[1], 0, 0.00, 1.15),
        (bones[2], 0, 0.00, 0.86),
    ]
    initial = (0.10, 0.0, 0.0, 0.44, 0.30)
    if digit == "thumb":
        parameters = [
            (bones[0], 0, -0.45, 0.82),
            (bones[0], 1, -0.78, 0.78),
            (bones[0], 2, -0.78, 0.78),
            (bones[1], 0, -0.10, 0.90),
            (bones[2], 0, -0.10, 0.70),
        ]
        initial = (0.08, 0.0, 0.0, 0.34, 0.22)
    for (bone, axis, _lo, _hi), value in zip(parameters, initial):
        bone.rotation_euler[axis] = value
    bpy.context.view_layer.update()

    def objective() -> tuple[float, Vector]:
        point = surface_world(hand, vertex)
        contact = (point - target).length_squared
        # Mild pose regularizer prevents exact-contact contortions when several
        # nearly equivalent solutions exist.
        regularizer = 0.000003 * sum(float(b.rotation_euler[i]) ** 2 for b, i, _lo, _hi in parameters)
        return contact + regularizer, point

    best, point = objective()
    evaluations = 1
    for step in (0.30, 0.16, 0.085, 0.044, 0.022, 0.011, 0.0055, 0.0028, 0.0014):
        for _ in range(5):
            improved = False
            for bone, axis, lower, upper in parameters:
                base = float(bone.rotation_euler[axis])
                local_value, local_cost, local_point = base, best, point
                for candidate in (base - step, base + step):
                    if not lower <= candidate <= upper:
                        continue
                    bone.rotation_euler[axis] = candidate
                    bpy.context.view_layer.update()
                    cost, candidate_point = objective()
                    evaluations += 1
                    if cost < local_cost:
                        local_value, local_cost, local_point = candidate, cost, candidate_point
                bone.rotation_euler[axis] = local_value
                bpy.context.view_layer.update()
                if local_cost + 1e-14 < best:
                    best, point, improved = local_cost, local_point, True
            if not improved:
                break
    point = surface_world(hand, vertex)
    for bone in bones:
        bone.keyframe_insert(data_path="rotation_euler", frame=1, group=bone.name)
    return {
        "surface_vertex": vertex,
        "target_world_m": [round(float(v), 7) for v in target],
        "surface_world_m": [round(float(v), 7) for v in point],
        "surface_error_m": round((point - target).length, 7),
        "evaluations": evaluations,
        "rotations_xyz_rad": {b.name: [round(float(v), 6) for v in b.rotation_euler] for b in bones},
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
    bpy.context.view_layer.update()

    solves = {}
    for digit, (vertex, target, string, fret) in CONTACTS.items():
        result = solve_surface(armature, hand, digit, vertex, target)
        result.update({"string": string, "fret": fret, "depression_m": 0.00185, "pad_fraction_behind_fret": 0.18})
        solves[digit] = result
    thumb = solve_surface(armature, hand, "thumb", THUMB[0], THUMB[1])
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
        "contact_side": (Vector((-0.42, -0.62, 1.42)), Vector((0.26, -0.39, 1.38)), 92.0, (1200, 900)),
    }
    renders = {}
    for label, (location, target, lens, resolution) in views.items():
        camera.location = location
        camera.data.lens = lens
        point_at(camera, target)
        scene.camera = camera
        scene.render.resolution_x, scene.render.resolution_y = resolution
        scene.render.resolution_percentage = 100
        path = RENDERS / f"v253_{label}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        renders[label] = {"path": str(path.relative_to(ROOT)), "sha256": sha256(path)}

    record = {
        "schema": "v253-surface-contact-fretting-v1",
        "status": "BUILT_VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha256(SOURCE)},
        "output": {"path": str(OUTPUT.relative_to(ROOT))},
        "wrist_delta_m": [round(float(v), 7) for v in WRIST_DELTA],
        "solves": solves,
        "thumb": thumb,
        "max_surface_error_m": max(v["surface_error_m"] for v in solves.values()),
        "renders": renders,
    }
    scene["V253_STATUS"] = "SURFACE_CONTACT_FRETTING_VISUAL_REVIEW_REQUIRED"
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record["output"]["sha256"] = sha256(OUTPUT)
    (AUDIT / "v253_surface_contact_fretting.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("V253_SURFACE_CONTACT_FRETTING_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
