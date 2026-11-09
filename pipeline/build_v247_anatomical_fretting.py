"""Replace V246's unconstrained contact solve with an anatomical fretting pose."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v245_arm_performance_pose" / "Character_An_arm_performance_v245.blend"
STAGE = ROOT / "production_v247_anatomical_fretting"
OUTPUT = STAGE / "Character_An_anatomical_fretting_v247.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"
RIG_NAME = "V239_CLEAN_CHARACTER_RIG"

CONTACTS = {
    "index": {"string": "S5", "fret": 9, "target": Vector((0.2671270, -0.4045161, 1.3946022))},
    "middle": {"string": "S4", "fret": 10, "target": Vector((0.2444796, -0.4026991, 1.3896780))},
    "ring": {"string": "S7", "fret": 9, "target": Vector((0.2757289, -0.4060766, 1.3818460))},
    "pinky": {"string": "S8", "fret": 11, "target": Vector((0.2460079, -0.4042325, 1.3534319))},
}
THUMB_TARGET = Vector((0.247, -0.315, 1.372))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def point_at(obj: bpy.types.Object, target: Vector) -> None:
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def tip_world(rig: bpy.types.Object, prefix: str) -> Vector:
    return rig.matrix_world @ rig.pose.bones[f"DEF-{prefix}.03.L"].tail


def solve_chain(rig: bpy.types.Object, prefix: str, target: Vector, thumb: bool = False) -> dict:
    controls = [rig.pose.bones[f"{prefix}.{joint}.L"] for joint in ("01", "02", "03")]
    for control in controls:
        control.rotation_mode = "XYZ"
        control.rotation_euler = (0.0, 0.0, 0.0)

    # Middle and distal joints flex around their anatomical hinge only.  Only
    # the MCP knuckle can spread or oppose, preventing the corkscrew collapse
    # produced by V246's unconstrained three-axis search.
    if thumb:
        initial = (0.18, 0.0, 0.0, 0.90, 0.72)
        bounds = ((-0.55, 0.85), (-0.55, 0.55), (-0.55, 0.55), (0.15, 1.45), (0.10, 1.35))
    else:
        initial = (0.20, 0.0, 0.0, 1.12, 0.82)
        bounds = ((-0.45, 0.85), (-0.48, 0.48), (-0.58, 0.58), (0.25, 1.62), (0.18, 1.38))
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

    def error_squared() -> float:
        return (tip_world(rig, prefix) - target).length_squared

    best = error_squared()
    evaluations = 1
    for step in (0.40, 0.22, 0.12, 0.065, 0.032, 0.016, 0.008, 0.004, 0.002):
        for _ in range(5):
            improved = False
            for index, (control, axis) in enumerate(parameters):
                base = float(control.rotation_euler[axis])
                local_value = base
                local_cost = best
                lower, upper = bounds[index]
                for candidate in (base - step, base + step):
                    if candidate < lower or candidate > upper:
                        continue
                    control.rotation_euler[axis] = candidate
                    bpy.context.view_layer.update()
                    candidate_cost = error_squared()
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

    final = tip_world(rig, prefix)
    for control in controls:
        control.keyframe_insert(data_path="rotation_euler", frame=1, group=control.name)
    return {
        "target_world_m": [round(float(value), 7) for value in target],
        "solved_tip_world_m": [round(float(value), 7) for value in final],
        "error_m": round((final - target).length, 7),
        "evaluations": evaluations,
        "hinge_only_middle_and_distal": True,
        "rotations_xyz_rad": {
            control.name: [round(float(value), 6) for value in control.rotation_euler]
            for control in controls
        },
    }


def main() -> None:
    if Path(bpy.data.filepath).resolve() != SOURCE.resolve():
        raise RuntimeError(f"Open V245 first: {SOURCE}")
    STAGE.mkdir(parents=True, exist_ok=True)
    RENDERS.mkdir(parents=True, exist_ok=True)
    AUDIT.mkdir(parents=True, exist_ok=True)
    rig = bpy.data.objects[RIG_NAME]
    solves = {}
    for digit, contact in CONTACTS.items():
        solves[digit] = {
            "string": contact["string"],
            "fret": contact["fret"],
            "depression_m": 0.00185,
            "pad_fraction_behind_fret": 0.18,
            **solve_chain(rig, f"f_{digit}", contact["target"]),
        }
    thumb = solve_chain(rig, "thumb", THUMB_TARGET, thumb=True)
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
        "fretting_close": (Vector((0.72, -1.48, 1.49)), Vector((0.27, -0.39, 1.39)), 105.0, (1200, 900)),
        "fretting_oblique": (Vector((0.86, -1.08, 1.25)), Vector((0.27, -0.39, 1.39)), 95.0, (1200, 900)),
    }
    render_records = {}
    for label, (location, target_point, lens, resolution) in views.items():
        camera.location = location
        camera.data.lens = lens
        point_at(camera, target_point)
        scene.camera = camera
        scene.render.resolution_x, scene.render.resolution_y = resolution
        scene.render.resolution_percentage = 100
        path = RENDERS / f"v247_{label}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        render_records[label] = {"path": str(path.relative_to(ROOT)), "sha256": sha256(path)}

    scene["V247_STATUS"] = "ANATOMICAL_FRETTING_SOLVE_VISUAL_REVIEW_REQUIRED"
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v247-anatomical-fretting-v1",
        "status": "BUILT_VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha256(SOURCE)},
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha256(OUTPUT)},
        "rig": RIG_NAME,
        "solves": solves,
        "thumb": thumb,
        "max_fingertip_error_m": max(value["error_m"] for value in solves.values()),
        "renders": render_records,
    }
    (AUDIT / "v247_anatomical_fretting.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("V247_ANATOMICAL_FRETTING_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
