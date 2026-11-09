"""Refine V301 pad contact without translating any individual finger root."""

from pathlib import Path
import json
import math

import bpy
from mathutils import Euler, Matrix, Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v301_global_continuous_fretting" / "Character_An_global_continuous_fretting_v301.blend"
STAGE = ROOT / "production_v302_fretting_contact_refinement"
OUTPUT = STAGE / "Character_An_fretting_contact_refinement_v302.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"
LIB = ROOT / "pipeline" / "build_v301_global_continuous_fretting.py"
namespace = {"__name__": "v301_library"}
exec(compile(LIB.read_text(), str(LIB), "exec"), namespace)


def refine(rig, hand, hub, neck, targets):
    contacts = namespace["CONTACTS"]
    thumb = namespace["THUMB"]
    surface_points = namespace["surface_points"]
    arc_penalty = namespace["arc_penalty"]
    base_hub = hub.matrix_world.copy()
    delta_translation = Vector((0.0, 0.0, 0.0))
    delta_rotation = Vector((0.0, 0.0, 0.0))
    digits = (*contacts.keys(), "thumb")
    vertex_indices = [value[0] for value in contacts.values()] + [thumb[0]]

    def update_hub():
        pivot = base_hub.translation
        rotate = Euler(delta_rotation, "XYZ").to_matrix().to_4x4()
        hub.matrix_world = Matrix.Translation(delta_translation) @ Matrix.Translation(pivot) @ rotate @ Matrix.Translation(-pivot) @ base_hub
        bpy.context.view_layer.update()

    variables = []
    for axis in range(3):
        variables.append(("hub", delta_translation, axis, -.020, .020, .006))
        variables.append(("hub", delta_rotation, axis, math.radians(-14), math.radians(14), math.radians(4.5)))
    for digit in digits:
        for joint in range(1, 4):
            bone = rig.pose.bones[f"{digit}_{joint:02d}"]
            bone.location = (0.0, 0.0, 0.0)
            bone.rotation_mode = "XYZ"
            x_bounds = (-.80, 1.15) if joint == 1 else ((-.20, 1.45) if joint == 2 else (-.20, 1.20))
            variables.append(("bone", bone.rotation_euler, 0, x_bounds[0], x_bounds[1], .095))
            lateral = .30 if joint == 1 else (.24 if joint == 2 else .18)
            variables.append(("bone", bone.rotation_euler, 1, -lateral, lateral, .070))
            variables.append(("bone", bone.rotation_euler, 2, -lateral, lateral, .070))

    def objective(detail=False):
        points = surface_points(hand, vertex_indices)
        errors = {}
        contact_sq = 0.0
        for digit, spec in contacts.items():
            error = (points[spec[0]] - targets[digit]).length
            errors[digit] = error
            contact_sq += error * error
        thumb_error = (points[thumb[0]] - targets["thumb"]).length
        errors["thumb"] = thumb_error
        contact_sq += thumb_error * thumb_error * .72
        collision = 0.0
        inside = {}
        for digit in digits:
            penalty, count, _samples = arc_penalty(rig, neck, digit)
            collision += penalty
            inside[digit] = count
        regularizer = delta_translation.length_squared * .04 + delta_rotation.length_squared * .0005
        value = contact_sq * 14000.0 + collision * 55.0 + regularizer
        if detail:
            return value, errors, inside, points
        return value

    update_hub()
    best = objective()
    evaluations = 1
    for scale in (1.0, .52, .27, .14, .07, .035, .018):
        for _pass in range(3):
            improved = False
            for kind, vector, axis, lower, upper, initial_step in variables:
                base = float(vector[axis])
                accepted, local_best = base, best
                step = initial_step * scale
                for candidate in (max(lower, base - step), min(upper, base + step)):
                    vector[axis] = candidate
                    update_hub() if kind == "hub" else bpy.context.view_layer.update()
                    value = objective()
                    evaluations += 1
                    if value < local_best:
                        accepted, local_best = candidate, value
                vector[axis] = accepted
                update_hub() if kind == "hub" else bpy.context.view_layer.update()
                if local_best + 1e-12 < best:
                    best = local_best
                    improved = True
            if not improved:
                break
    value, errors, inside, points = objective(detail=True)
    return {
        "evaluations": evaluations,
        "objective": float(value),
        "hub_delta_translation_m": [float(v) for v in delta_translation],
        "hub_delta_rotation_rad": [float(v) for v in delta_rotation],
        "surface_errors_m": {name: float(value) for name, value in errors.items()},
        "inside_samples": inside,
        "surface_world": {digit: [float(v) for v in points[spec[0]]] for digit, spec in contacts.items()},
        "thumb_surface_world": [float(v) for v in points[thumb[0]]],
        "rotations": {
            f"{digit}_{joint:02d}": [float(v) for v in rig.pose.bones[f"{digit}_{joint:02d}"].rotation_euler]
            for digit in digits for joint in range(1, 4)
        },
    }


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    for folder in (STAGE, RENDERS, AUDIT):
        folder.mkdir(parents=True, exist_ok=True)
    rig = bpy.data.objects[namespace["RIG"]]
    hand = bpy.data.objects[namespace["HAND"]]
    hub = bpy.data.objects[namespace["HUB"]]
    neck = bpy.data.objects[namespace["NECK"]]
    contacts = namespace["CONTACTS"]
    thumb = namespace["THUMB"]
    targets = {digit: namespace["target_world"](neck, spec) for digit, spec in contacts.items()}
    targets["thumb"] = neck.matrix_world @ thumb[1]
    result = refine(rig, hand, hub, neck, targets)
    bpy.context.view_layer.update()

    scene = bpy.context.scene
    camera = bpy.data.objects["V287_GUITAR_CAMERA"]
    focus = Vector((.262, -.397, 1.383))
    views = {
        "full": (Vector((0.0, -3.75, 1.02)), Vector((0.0, -.02, 1.0)), 66.0, (900, 1000)),
        "contact_front": (Vector((.72, -1.48, 1.49)), focus, 105.0, (1200, 900)),
        "contact_oblique": (Vector((.86, -.92, 1.66)), focus, 110.0, (1200, 900)),
        "contact_player": (Vector((-.18, -.92, 1.58)), focus, 108.0, (1200, 900)),
    }
    renders = {
        label: namespace["render"](scene, camera, RENDERS / f"v302_{label}.png", *settings)
        for label, settings in views.items()
    }
    max_error = max(result["surface_errors_m"][digit] for digit in contacts)
    status = "VISUAL_REVIEW_REQUIRED" if max_error <= .0025 else "REJECT_CONTACT_ERROR"
    scene["V302_STATUS"] = status
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v302-fretting-contact-refinement-v1",
        "status": status,
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": namespace["sha"](SOURCE)},
        "targets": {name: [float(v) for v in value] for name, value in targets.items()},
        "solve": result,
        "renders": renders,
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": namespace["sha"](OUTPUT)},
    }
    (AUDIT / "v302_fretting_contact_refinement.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V302_FRETTING_CONTACT_REFINEMENT_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
