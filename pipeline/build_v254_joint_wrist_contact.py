"""Jointly fit the fretting wrist to all pad targets, then refine safe finger flexion."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import bpy
from mathutils import Euler, Matrix, Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v250_dedicated_hand_rig" / "Character_An_dedicated_hand_rig_v250.blend"
STAGE = ROOT / "production_v254_joint_wrist_contact"
OUTPUT = STAGE / "Character_An_joint_wrist_contact_v254.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"
MAIN_RIG = "V239_CLEAN_CHARACTER_RIG"
ARMATURE = "V250_FRETTING_HAND_RIG"
HAND = "V248_FRETTING_HAND_REALISTIC"
CONTACTS = {
    "index": (233, Vector((0.2671270, -0.4045161, 1.3946022)), "S5", 9),
    "middle": (213, Vector((0.2444796, -0.4026991, 1.3896780)), "S4", 10),
    "ring": (13, Vector((0.2757289, -0.4060766, 1.3818460)), "S7", 9),
    "pinky": (1, Vector((0.2460079, -0.4042325, 1.3534319)), "S8", 11),
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def point_at(obj, target: Vector) -> None:
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def surface_world(hand, vertex_index: int) -> Vector:
    dg = bpy.context.evaluated_depsgraph_get()
    evaluated = hand.evaluated_get(dg)
    mesh = evaluated.to_mesh()
    try:
        return evaluated.matrix_world @ mesh.vertices[vertex_index].co
    finally:
        evaluated.to_mesh_clear()


def main() -> None:
    if Path(bpy.data.filepath).resolve() != SOURCE.resolve():
        raise RuntimeError(f"Open V250 first: {SOURCE}")
    STAGE.mkdir(parents=True, exist_ok=True)
    RENDERS.mkdir(parents=True, exist_ok=True)
    AUDIT.mkdir(parents=True, exist_ok=True)
    rig = bpy.data.objects[MAIN_RIG]
    arm = bpy.data.objects[ARMATURE]
    hand = bpy.data.objects[HAND]
    bpy.context.scene.frame_set(1)

    # Establish a natural flex before solving the wrist. This prevents the
    # global fit from using an anatomically irrelevant open-hand footprint.
    for digit in CONTACTS:
        for joint, angle in enumerate((0.12, 0.48, 0.32), 1):
            bone = arm.pose.bones[f"{digit}_{joint:02d}"]
            bone.rotation_mode = "XYZ"
            bone.rotation_euler = (angle, 0.0, 0.0)
    bpy.context.view_layer.update()

    hand_ik = rig.pose.bones["hand_ik.L"]
    base_world = rig.matrix_world @ hand_ik.matrix
    base_loc, base_rot, base_scale = base_world.decompose()
    params = [0.0] * 6
    bounds = [(-0.10, 0.05), (-0.02, 0.12), (-0.09, 0.05), (-0.65, 0.65), (-0.65, 0.65), (-0.65, 0.65)]

    def apply_wrist() -> None:
        delta_rot = Euler(params[3:6], "XYZ").to_quaternion()
        world = Matrix.LocRotScale(base_loc + Vector(params[:3]), delta_rot @ base_rot, base_scale)
        hand_ik.matrix = rig.matrix_world.inverted() @ world
        bpy.context.view_layer.update()

    def global_cost() -> float:
        total = 0.0
        for vertex, target, _string, _fret in CONTACTS.values():
            error = surface_world(hand, vertex) - target
            total += error.length_squared
        total += 0.00002 * sum(v * v for v in params[3:6])
        return total

    apply_wrist()
    best = global_cost()
    evaluations = 1
    for step in (0.08, 0.04, 0.02, 0.01, 0.005, 0.0025, 0.00125, 0.0006):
        for _ in range(4):
            improved = False
            for i, (lower, upper) in enumerate(bounds):
                base = params[i]
                local_value, local_cost = base, best
                candidates = (base - step, base + step) if i < 3 else (base - step * 4.0, base + step * 4.0)
                for candidate in candidates:
                    if not lower <= candidate <= upper:
                        continue
                    params[i] = candidate
                    apply_wrist()
                    cost = global_cost()
                    evaluations += 1
                    if cost < local_cost:
                        local_value, local_cost = candidate, cost
                params[i] = local_value
                apply_wrist()
                if local_cost + 1e-14 < best:
                    best, improved = local_cost, True
            if not improved:
                break

    # Refine each digit with conservative MCP spread and ordinary hinge flex.
    solves = {}
    for digit, (vertex, target, string, fret) in CONTACTS.items():
        bones = [arm.pose.bones[f"{digit}_{j:02d}"] for j in range(1, 4)]
        digit_params = [
            (bones[0], 0, -0.10, 0.72),
            (bones[0], 1, -0.25, 0.25),
            (bones[0], 2, -0.18, 0.18),
            (bones[1], 0, 0.05, 1.05),
            (bones[2], 0, 0.02, 0.78),
        ]

        def cost() -> float:
            return (surface_world(hand, vertex) - target).length_squared

        local_best = cost()
        local_evals = 1
        for step in (0.22, 0.11, 0.055, 0.028, 0.014, 0.007, 0.0035, 0.0017):
            for _ in range(4):
                improved = False
                for bone, axis, lower, upper in digit_params:
                    base = float(bone.rotation_euler[axis])
                    value, value_cost = base, local_best
                    for candidate in (base - step, base + step):
                        if not lower <= candidate <= upper:
                            continue
                        bone.rotation_euler[axis] = candidate
                        bpy.context.view_layer.update()
                        candidate_cost = cost()
                        local_evals += 1
                        if candidate_cost < value_cost:
                            value, value_cost = candidate, candidate_cost
                    bone.rotation_euler[axis] = value
                    bpy.context.view_layer.update()
                    if value_cost + 1e-14 < local_best:
                        local_best, improved = value_cost, True
                if not improved:
                    break
        point = surface_world(hand, vertex)
        for bone in bones:
            bone.keyframe_insert(data_path="rotation_euler", frame=1, group=bone.name)
        solves[digit] = {
            "surface_vertex": vertex,
            "string": string,
            "fret": fret,
            "target_world_m": [round(float(v), 7) for v in target],
            "surface_world_m": [round(float(v), 7) for v in point],
            "surface_error_m": round((point - target).length, 7),
            "evaluations": local_evals,
            "rotations_xyz_rad": {b.name: [round(float(v), 6) for v in b.rotation_euler] for b in bones},
        }
    hand_ik.keyframe_insert(data_path="location", frame=1, group=hand_ik.name)
    if hand_ik.rotation_mode == "QUATERNION":
        hand_ik.keyframe_insert(data_path="rotation_quaternion", frame=1, group=hand_ik.name)
    else:
        hand_ik.keyframe_insert(data_path="rotation_euler", frame=1, group=hand_ik.name)

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.look = "AgX - Medium High Contrast"
    camera = bpy.data.objects["CAM_V211_FRONT"]
    camera.data.type = "PERSP"
    views = {
        "contact_front": (Vector((0.72, -1.48, 1.49)), Vector((0.27, -0.39, 1.39)), 105.0),
        "contact_oblique": (Vector((0.86, -1.08, 1.25)), Vector((0.27, -0.39, 1.39)), 95.0),
        "player_side": (Vector((0.58, 0.20, 1.40)), Vector((0.27, -0.37, 1.38)), 90.0),
    }
    renders = {}
    for label, (location, target, lens) in views.items():
        camera.location, camera.data.lens = location, lens
        point_at(camera, target)
        scene.camera = camera
        scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = 1200, 900, 100
        path = RENDERS / f"v254_{label}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        renders[label] = {"path": str(path.relative_to(ROOT)), "sha256": sha256(path)}

    record = {
        "schema": "v254-joint-wrist-contact-v1",
        "status": "BUILT_VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha256(SOURCE)},
        "wrist_parameters": [round(float(v), 7) for v in params],
        "wrist_evaluations": evaluations,
        "solves": solves,
        "max_surface_error_m": max(v["surface_error_m"] for v in solves.values()),
        "renders": renders,
        "output": {"path": str(OUTPUT.relative_to(ROOT))},
    }
    scene["V254_STATUS"] = "JOINT_WRIST_CONTACT_VISUAL_REVIEW_REQUIRED"
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record["output"]["sha256"] = sha256(OUTPUT)
    (AUDIT / "v254_joint_wrist_contact.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("V254_JOINT_WRIST_CONTACT_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
