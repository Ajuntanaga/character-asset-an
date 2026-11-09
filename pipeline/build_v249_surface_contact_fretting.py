"""Solve V248's realistic hand using rendered fingertip surface landmarks."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v248_topology_hand_replacement" / "Character_An_topology_hand_v248.blend"
STAGE = ROOT / "production_v249_surface_contact_fretting"
OUTPUT = STAGE / "Character_An_surface_contact_v249.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"
RIG_NAME = "V239_CLEAN_CHARACTER_RIG"
HAND_NAME = "V248_FRETTING_HAND_REALISTIC"

CONTACTS = {
    "index": {"vertex": 241, "string": "S5", "fret": 9, "target": Vector((0.2671270, -0.4045161, 1.3946022))},
    "middle": {"vertex": 211, "string": "S4", "fret": 10, "target": Vector((0.2444796, -0.4026991, 1.3896780))},
    "ring": {"vertex": 49, "string": "S7", "fret": 9, "target": Vector((0.2757289, -0.4060766, 1.3818460))},
    "pinky": {"vertex": 280, "string": "S8", "fret": 11, "target": Vector((0.2460079, -0.4042325, 1.3534319))},
}
THUMB = {"vertex": 154, "target": Vector((0.247, -0.315, 1.372))}


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
    rig: bpy.types.Object,
    hand: bpy.types.Object,
    prefix: str,
    vertex_index: int,
    target: Vector,
    thumb: bool = False,
) -> dict:
    controls = [rig.pose.bones[f"{prefix}.{joint}.L"] for joint in ("01", "02", "03")]
    for control in controls:
        control.rotation_mode = "XYZ"
        control.rotation_euler = (0.0, 0.0, 0.0)
    if thumb:
        initial = (0.10, 0.0, 0.0, 0.85, 0.62)
        bounds = ((-0.65, 0.85), (-0.65, 0.65), (-0.70, 0.70), (0.10, 1.50), (0.08, 1.35))
    else:
        initial = (0.18, 0.0, 0.0, 1.00, 0.70)
        bounds = ((-0.50, 0.88), (-0.52, 0.52), (-0.62, 0.62), (0.20, 1.58), (0.15, 1.30))
    parameters = [
        (controls[0], 0),
        (controls[0], 1),
        (controls[0], 2),
        (controls[1], 0),
        (controls[2], 0),
    ]
    for (control, axis), value in zip(parameters, initial):
        control.rotation_euler[axis] = value
    bpy.context.view_layer.update()

    def cost() -> float:
        return (surface_world(hand, vertex_index) - target).length_squared

    best = cost()
    evaluations = 1
    for step in (0.38, 0.20, 0.105, 0.055, 0.028, 0.014, 0.007, 0.0035):
        for _ in range(4):
            improved = False
            for index, (control, axis) in enumerate(parameters):
                base = float(control.rotation_euler[axis])
                lower, upper = bounds[index]
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
    point = surface_world(hand, vertex_index)
    for control in controls:
        control.keyframe_insert(data_path="rotation_euler", frame=1, group=control.name)
    return {
        "surface_vertex": vertex_index,
        "target_world_m": [round(float(value), 7) for value in target],
        "surface_world_m": [round(float(value), 7) for value in point],
        "error_m": round((point - target).length, 7),
        "evaluations": evaluations,
        "rotations_xyz_rad": {
            control.name: [round(float(value), 6) for value in control.rotation_euler]
            for control in controls
        },
    }


def main() -> None:
    if Path(bpy.data.filepath).resolve() != SOURCE.resolve():
        raise RuntimeError(f"Open V248 first: {SOURCE}")
    STAGE.mkdir(parents=True, exist_ok=True)
    RENDERS.mkdir(parents=True, exist_ok=True)
    AUDIT.mkdir(parents=True, exist_ok=True)
    rig = bpy.data.objects[RIG_NAME]
    hand = bpy.data.objects[HAND_NAME]
    solves = {}
    for digit, contact in CONTACTS.items():
        solves[digit] = {
            "string": contact["string"],
            "fret": contact["fret"],
            "depression_m": 0.00185,
            "pad_fraction_behind_fret": 0.18,
            **solve_chain(rig, hand, f"f_{digit}", contact["vertex"], contact["target"]),
        }
    thumb = solve_chain(rig, hand, "thumb", THUMB["vertex"], THUMB["target"], thumb=True)
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
        path = RENDERS / f"v249_{label}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        render_records[label] = {"path": str(path.relative_to(ROOT)), "sha256": sha256(path)}

    scene["V249_STATUS"] = "REALISTIC_HAND_SURFACE_CONTACT_SOLVE_VISUAL_REVIEW_REQUIRED"
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v249-surface-contact-fretting-v1",
        "status": "BUILT_VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha256(SOURCE)},
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha256(OUTPUT)},
        "hand": HAND_NAME,
        "solves": solves,
        "thumb": thumb,
        "max_surface_error_m": max(value["error_m"] for value in solves.values()),
        "renders": render_records,
    }
    (AUDIT / "v249_surface_contact.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("V249_SURFACE_CONTACT_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
