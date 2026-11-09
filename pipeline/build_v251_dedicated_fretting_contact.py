"""Solve V250's dedicated hand rig to the protected V237 fretting contacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v250_dedicated_hand_rig" / "Character_An_dedicated_hand_rig_v250.blend"
STAGE = ROOT / "production_v251_dedicated_fretting_contact"
OUTPUT = STAGE / "Character_An_fretting_contact_v251.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"
ARMATURE_NAME = "V250_FRETTING_HAND_RIG"
HAND_NAME = "V248_FRETTING_HAND_REALISTIC"

CONTACTS = {
    "index": {"vertex": 233, "string": "S5", "fret": 9, "target": Vector((0.2671270, -0.4045161, 1.3946022))},
    "middle": {"vertex": 213, "string": "S4", "fret": 10, "target": Vector((0.2444796, -0.4026991, 1.3896780))},
    "ring": {"vertex": 13, "string": "S7", "fret": 9, "target": Vector((0.2757289, -0.4060766, 1.3818460))},
    "pinky": {"vertex": 1, "string": "S8", "fret": 11, "target": Vector((0.2460079, -0.4042325, 1.3534319))},
}
THUMB = {"vertex": 695, "target": Vector((0.247, -0.315, 1.372))}


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


def solve_chain(
    armature: bpy.types.Object,
    hand: bpy.types.Object,
    digit: str,
    target: Vector,
    vertex_index: int,
    surface_cost: bool = False,
) -> dict:
    controls = [armature.pose.bones[f"{digit}_{joint:02d}"] for joint in range(1, 4)]
    for control in controls:
        control.rotation_mode = "XYZ"
        control.rotation_euler = (0.0, 0.0, 0.0)
    initial = (0.20, 0.0, 0.0, 0.82, 0.50)
    if digit == "thumb":
        initial = (0.14, 0.0, 0.0, 0.52, 0.34)
    parameters = [
        (controls[0], 0, -0.55, 1.20),
        (controls[0], 1, -0.75, 0.75),
        (controls[0], 2, -0.75, 0.75),
        (controls[1], 0, 0.00, 1.70),
        (controls[2], 0, 0.00, 1.50),
    ]
    for (control, axis, _lower, _upper), value in zip(parameters, initial):
        control.rotation_euler[axis] = value
    bpy.context.view_layer.update()

    def current() -> Vector:
        if surface_cost:
            return surface_world(hand, vertex_index)
        return armature.matrix_world @ controls[-1].tail

    def cost() -> float:
        return (current() - target).length_squared

    best = cost()
    evaluations = 1
    for step in (0.42, 0.23, 0.12, 0.062, 0.031, 0.016, 0.008, 0.004, 0.002):
        for _ in range(5):
            improved = False
            for control, axis, lower, upper in parameters:
                base = float(control.rotation_euler[axis])
                local_value = base
                local_cost = best
                for candidate in (base - step, base + step):
                    if candidate < lower or candidate > upper:
                        continue
                    control.rotation_euler[axis] = candidate
                    bpy.context.view_layer.update()
                    candidate_cost = cost()
                    evaluations += 1
                    if candidate_cost < local_cost:
                        local_cost = candidate_cost
                        local_value = candidate
                control.rotation_euler[axis] = local_value
                bpy.context.view_layer.update()
                if local_cost + 1e-14 < best:
                    best = local_cost
                    improved = True
            if not improved:
                break
    bone_tip = armature.matrix_world @ controls[-1].tail
    surface = surface_world(hand, vertex_index)
    for control in controls:
        control.keyframe_insert(data_path="rotation_euler", frame=1, group=control.name)
    return {
        "surface_vertex": vertex_index,
        "target_world_m": [round(float(value), 7) for value in target],
        "bone_tip_world_m": [round(float(value), 7) for value in bone_tip],
        "surface_world_m": [round(float(value), 7) for value in surface],
        "bone_error_m": round((bone_tip - target).length, 7),
        "surface_error_m": round((surface - target).length, 7),
        "evaluations": evaluations,
        "surface_optimized": surface_cost,
        "rotations_xyz_rad": {
            control.name: [round(float(value), 6) for value in control.rotation_euler]
            for control in controls
        },
    }


def main() -> None:
    if Path(bpy.data.filepath).resolve() != SOURCE.resolve():
        raise RuntimeError(f"Open V250 first: {SOURCE}")
    STAGE.mkdir(parents=True, exist_ok=True)
    RENDERS.mkdir(parents=True, exist_ok=True)
    AUDIT.mkdir(parents=True, exist_ok=True)
    armature = bpy.data.objects[ARMATURE_NAME]
    hand = bpy.data.objects[HAND_NAME]
    solves = {}
    for digit, contact in CONTACTS.items():
        solves[digit] = {
            "string": contact["string"],
            "fret": contact["fret"],
            "depression_m": 0.00185,
            "pad_fraction_behind_fret": 0.18,
            **solve_chain(armature, hand, digit, contact["target"], contact["vertex"]),
        }
    thumb = solve_chain(armature, hand, "thumb", THUMB["target"], THUMB["vertex"], surface_cost=True)
    thumb["constraint"] = "behind neck"
    bpy.context.view_layer.update()

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
        path = RENDERS / f"v251_{label}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        render_records[label] = {"path": str(path.relative_to(ROOT)), "sha256": sha256(path)}

    scene["V251_STATUS"] = "DEDICATED_HAND_V237_CONTACTS_VISUAL_REVIEW_REQUIRED"
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v251-dedicated-fretting-contact-v1",
        "status": "BUILT_VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha256(SOURCE)},
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha256(OUTPUT)},
        "armature": ARMATURE_NAME,
        "solves": solves,
        "thumb": thumb,
        "max_surface_error_m": max(value["surface_error_m"] for value in solves.values()),
        "renders": render_records,
    }
    (AUDIT / "v251_fretting_contact.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("V251_FRETTING_CONTACT_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
