"""Route the continuous fretting hand around the neck edge instead of through it."""

from pathlib import Path
import json
import math

import bpy
from mathutils import Euler, Matrix, Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v302_fretting_contact_refinement" / "Character_An_fretting_contact_refinement_v302.blend"
STAGE = ROOT / "production_v303_anatomical_fretting_route"
OUTPUT = STAGE / "Character_An_anatomical_fretting_route_v303.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"
LIB = ROOT / "pipeline" / "build_v301_global_continuous_fretting.py"
ns = {"__name__": "v301_library"}
exec(compile(LIB.read_text(), str(LIB), "exec"), ns)


def sq_positive(value):
    return max(0.0, value) ** 2


def solve(rig, hand, hub, neck, targets):
    contacts = ns["CONTACTS"]
    thumb = ns["THUMB"]
    surface_points = ns["surface_points"]
    base_hub = hub.matrix_world.copy()
    hub_t = Vector((0.0, 0.0, 0.0))
    hub_r = Vector((0.0, 0.0, 0.0))
    digits = (*contacts.keys(), "thumb")
    vertex_indices = [spec[0] for spec in contacts.values()] + [thumb[0]]

    variables = []
    for axis in range(3):
        variables.append(("hub", hub_t, axis, -.025, .025, .006))
        variables.append(("hub", hub_r, axis, math.radians(-16), math.radians(16), math.radians(4)))
    for digit in digits:
        for joint in range(1, 4):
            bone = rig.pose.bones[f"{digit}_{joint:02d}"]
            bone.location = (0.0, 0.0, 0.0)
            bone.rotation_mode = "XYZ"
            xb = (-.90, 1.30) if joint == 1 else ((-.25, 1.55) if joint == 2 else (-.25, 1.30))
            variables.append(("bone", bone.rotation_euler, 0, xb[0], xb[1], .09))
            lateral = .38 if joint == 1 else (.32 if joint == 2 else .24)
            variables.append(("bone", bone.rotation_euler, 1, -lateral, lateral, .065))
            variables.append(("bone", bone.rotation_euler, 2, -lateral, lateral, .065))

    def update_hub():
        pivot = base_hub.translation
        rotation = Euler(hub_r, "XYZ").to_matrix().to_4x4()
        hub.matrix_world = Matrix.Translation(hub_t) @ Matrix.Translation(pivot) @ rotation @ Matrix.Translation(-pivot) @ base_hub
        bpy.context.view_layer.update()

    def anatomy_penalty(detail=False):
        to_neck = neck.matrix_world.inverted()
        value = 0.0
        samples = {}
        for digit in contacts:
            b1 = rig.pose.bones[f"{digit}_01"]
            b2 = rig.pose.bones[f"{digit}_02"]
            b3 = rig.pose.bones[f"{digit}_03"]
            pts = [
                to_neck @ (rig.matrix_world @ b1.head),
                to_neck @ (rig.matrix_world @ b1.tail),
                to_neck @ (rig.matrix_world @ b2.tail),
                to_neck @ (rig.matrix_world @ b3.head),
            ]
            # MCP and proximal phalanx stay behind the neck and outside its
            # positive-Y edge; only the distal arc crosses onto the strings.
            value += 2.4 * sq_positive(.058 - pts[0].y)
            value += 2.0 * sq_positive(.057 - pts[1].y)
            value += 1.3 * sq_positive(.050 - pts[2].y)
            value += .7 * sq_positive(.043 - pts[3].y)
            value += 1.4 * sq_positive(pts[0].z + .030)
            value += .8 * sq_positive(pts[1].z + .010)
            samples[digit] = [list(p) for p in pts]
        tb1 = rig.pose.bones["thumb_01"]
        tb2 = rig.pose.bones["thumb_02"]
        tpts = [
            to_neck @ (rig.matrix_world @ tb1.head),
            to_neck @ (rig.matrix_world @ tb1.tail),
            to_neck @ (rig.matrix_world @ tb2.tail),
        ]
        value += 2.0 * sum(sq_positive(p.z + .032) for p in tpts[:2])
        value += .5 * sum(max(0.0, abs(p.y) - .045) ** 2 for p in tpts)
        samples["thumb"] = [list(p) for p in tpts]
        return (value, samples) if detail else value

    def objective(detail=False):
        points = surface_points(hand, vertex_indices)
        errors = {}
        contact = 0.0
        for digit, spec in contacts.items():
            error = (points[spec[0]] - targets[digit]).length
            errors[digit] = error
            contact += error * error
        thumb_error = (points[thumb[0]] - targets["thumb"]).length
        errors["thumb"] = thumb_error
        contact += .55 * thumb_error * thumb_error
        route, samples = anatomy_penalty(detail=True)
        regularizer = .02 * hub_t.length_squared + .0004 * hub_r.length_squared
        value = 12000.0 * contact + 1100.0 * route + regularizer
        if detail:
            return value, errors, route, samples, points
        return value

    update_hub()
    best = objective()
    evaluations = 1
    for scale in (1.0, .55, .30, .16, .085, .045, .024, .012):
        for _pass in range(4):
            improved = False
            for kind, vector, axis, lower, upper, initial in variables:
                base = float(vector[axis])
                accepted, local_best = base, best
                step = initial * scale
                for candidate in (max(lower, base - step), min(upper, base + step)):
                    vector[axis] = candidate
                    update_hub() if kind == "hub" else bpy.context.view_layer.update()
                    score = objective()
                    evaluations += 1
                    if score < local_best:
                        accepted, local_best = candidate, score
                vector[axis] = accepted
                update_hub() if kind == "hub" else bpy.context.view_layer.update()
                if local_best + 1e-12 < best:
                    best = local_best
                    improved = True
            if not improved:
                break
    value, errors, route, samples, points = objective(detail=True)
    return {
        "evaluations": evaluations,
        "objective": float(value),
        "route_penalty": float(route),
        "hub_translation_m": list(hub_t),
        "hub_rotation_rad": list(hub_r),
        "surface_errors_m": {key: float(value) for key, value in errors.items()},
        "route_samples_neck_local": samples,
        "surface_world": {digit: list(points[spec[0]]) for digit, spec in contacts.items()},
        "thumb_surface_world": list(points[thumb[0]]),
    }


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    for folder in (STAGE, RENDERS, AUDIT):
        folder.mkdir(parents=True, exist_ok=True)
    rig = bpy.data.objects[ns["RIG"]]
    hand = bpy.data.objects[ns["HAND"]]
    hub = bpy.data.objects[ns["HUB"]]
    neck = bpy.data.objects[ns["NECK"]]
    targets = {digit: ns["target_world"](neck, spec) for digit, spec in ns["CONTACTS"].items()}
    targets["thumb"] = neck.matrix_world @ ns["THUMB"][1]
    result = solve(rig, hand, hub, neck, targets)

    scene = bpy.context.scene
    camera = bpy.data.objects["V287_GUITAR_CAMERA"]
    focus = Vector((.262, -.397, 1.383))
    views = {
        "contact_front": (Vector((.72, -1.48, 1.49)), focus, 105.0, (1200, 900)),
        "contact_player": (Vector((-.18, -.92, 1.58)), focus, 108.0, (1200, 900)),
        "contact_rear": (Vector((.34, -.06, 1.30)), focus, 108.0, (1200, 900)),
        "contact_edge": (Vector((.48, -.34, 1.62)), focus, 112.0, (1200, 900)),
        "full": (Vector((0.0, -3.75, 1.02)), Vector((0.0, -.02, 1.0)), 66.0, (900, 1000)),
    }
    renders = {label: ns["render"](scene, camera, RENDERS / f"v303_{label}.png", *settings) for label, settings in views.items()}
    max_error = max(result["surface_errors_m"][digit] for digit in ns["CONTACTS"])
    status = "VISUAL_REVIEW_REQUIRED" if max_error <= .006 and result["route_penalty"] <= .0008 else "REJECT_GEOMETRY"
    scene["V303_STATUS"] = status
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v303-anatomical-fretting-route-v1",
        "status": status,
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": ns["sha"](SOURCE)},
        "solve": result,
        "renders": renders,
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": ns["sha"](OUTPUT)},
    }
    (AUDIT / "v303_anatomical_fretting_route.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V303_ANATOMICAL_FRETTING_ROUTE_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
