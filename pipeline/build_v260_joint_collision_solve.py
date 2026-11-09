"""Jointly optimize wrist and digit chains under real guitar collision."""

from pathlib import Path
import hashlib
import json
import bpy
from mathutils import Euler, Matrix, Vector

ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v258_collision_aware_fretting" / "Character_An_collision_aware_fretting_v258.blend"
STAGE = ROOT / "production_v260_joint_collision_solve"
OUTPUT = STAGE / "Character_An_joint_collision_solve_v260.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"

LIB = ROOT / "pipeline" / "build_v258_collision_aware_fretting.py"
module = {"__name__": "v258_collision_library"}
exec(compile(LIB.read_text(encoding="utf-8"), str(LIB), "exec"), module)
module["configure"]()
base = module["ns"]


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def point_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def main():
    if Path(bpy.data.filepath).resolve() != SOURCE.resolve():
        raise RuntimeError(f"Open V258 first: {SOURCE}")
    STAGE.mkdir(parents=True, exist_ok=True); RENDERS.mkdir(parents=True, exist_ok=True); AUDIT.mkdir(parents=True, exist_ok=True)
    rig = bpy.data.objects["V239_CLEAN_CHARACTER_RIG"]
    arm = bpy.data.objects["V250_FRETTING_HAND_RIG"]
    hand = bpy.data.objects["V248_FRETTING_HAND_REALISTIC"]
    neck = bpy.data.objects["V206_NECK"]
    neck_inv = neck.matrix_world.inverted()
    contacts = base["CONTACTS"]
    thumb_vertex, thumb_target = base["THUMB"]
    hand_ik = rig.pose.bones["hand_ik.L"]
    base_world = rig.matrix_world @ hand_ik.matrix
    base_loc, base_rot, base_scale = base_world.decompose()
    wrist = [0.0] * 6

    def apply_wrist():
        rotation = Euler(wrist[3:6], "XYZ").to_quaternion() @ base_rot
        hand_ik.matrix = rig.matrix_world.inverted() @ Matrix.LocRotScale(base_loc + Vector(wrist[:3]), rotation, base_scale)
        bpy.context.view_layer.update()

    def collision_total():
        total = 0.0
        for digit in ("index", "middle", "ring", "pinky", "thumb"):
            for j in range(1, 4):
                bone = arm.pose.bones[f"{digit}_{j:02d}"]
                head = arm.matrix_world @ bone.head; tail = arm.matrix_world @ bone.tail
                for fraction in (0.0, 0.25, 0.5, 0.75, 1.0):
                    depth = module["collision_depth"](neck_inv @ head.lerp(tail, fraction))
                    total += depth * depth
        return total

    def global_objective():
        contact_cost = 0.0
        for digit, (vertex, target, _string, _fret) in contacts.items():
            contact_cost += (base["surface_world"](hand, vertex) - target).length_squared
        contact_cost += (base["surface_world"](hand, thumb_vertex) - thumb_target).length_squared
        collision = collision_total()
        regularizer = 0.00001 * sum(value * value for value in wrist[3:6])
        return contact_cost + 60.0 * collision + regularizer, contact_cost, collision

    def optimize_wrist():
        apply_wrist()
        best, contact_cost, collision = global_objective(); evaluations = 1
        schedule = ((0.020, 0.14), (0.010, 0.075), (0.005, 0.038), (0.0025, 0.019), (0.00125, 0.0095), (0.0006, 0.0048))
        bounds = [(-0.06, 0.06)] * 3 + [(-0.55, 0.55)] * 3
        for translation_step, rotation_step in schedule:
            for _ in range(4):
                improved = False
                for i, (lower, upper) in enumerate(bounds):
                    step = translation_step if i < 3 else rotation_step
                    old = wrist[i]; value = old; value_cost = best; value_contact = contact_cost; value_collision = collision
                    for candidate in (old - step, old + step):
                        if not lower <= candidate <= upper:
                            continue
                        wrist[i] = candidate; apply_wrist()
                        cost, candidate_contact, candidate_collision = global_objective(); evaluations += 1
                        if cost < value_cost:
                            value, value_cost = candidate, cost
                            value_contact, value_collision = candidate_contact, candidate_collision
                    wrist[i] = value; apply_wrist()
                    if value_cost + 1e-14 < best:
                        best, contact_cost, collision, improved = value_cost, value_contact, value_collision, True
                if not improved:
                    break
        return {"evaluations": evaluations, "objective": best, "contact_cost": contact_cost, "collision": collision,
                "parameters": [round(float(v), 7) for v in wrist]}

    passes = []
    solves = {}
    for pass_index in range(2):
        passes.append(optimize_wrist())
        for digit, (vertex, target, string, fret) in contacts.items():
            result = module["solve_collision"](arm, hand, digit, vertex, target)
            result.update({"string": string, "fret": fret})
            solves[digit] = result
        solves["thumb"] = module["solve_collision"](arm, hand, "thumb", thumb_vertex, thumb_target)

    hand_ik.keyframe_insert(data_path="location", frame=1, group=hand_ik.name)
    if hand_ik.rotation_mode == "QUATERNION":
        hand_ik.keyframe_insert(data_path="rotation_quaternion", frame=1, group=hand_ik.name)
    else:
        hand_ik.keyframe_insert(data_path="rotation_euler", frame=1, group=hand_ik.name)

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"; scene.render.image_settings.file_format = "PNG"; scene.view_settings.look = "AgX - Medium High Contrast"
    camera = bpy.data.objects["CAM_V211_FRONT"]
    views = {
        "front": (Vector((0.72, -1.48, 1.49)), Vector((0.27, -0.39, 1.39)), 105.0),
        "oblique": (Vector((0.86, -1.08, 1.25)), Vector((0.27, -0.39, 1.39)), 95.0),
        "player_side": (Vector((0.58, 0.20, 1.40)), Vector((0.27, -0.37, 1.38)), 90.0),
    }
    renders = {}
    for label, (location, target, lens) in views.items():
        camera.location = location; camera.data.lens = lens; point_at(camera, target); scene.camera = camera
        scene.render.resolution_x = 1200; scene.render.resolution_y = 900; scene.render.resolution_percentage = 100
        path = RENDERS / f"v260_{label}.png"; scene.render.filepath = str(path); bpy.ops.render.render(write_still=True)
        renders[label] = {"path": str(path.relative_to(ROOT)), "sha256": sha256(path)}

    final_cost, final_contact_cost, final_collision = global_objective()
    record = {"schema": "v260-joint-collision-solve-v1", "status": "BUILT_VISUAL_REVIEW_REQUIRED",
              "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha256(SOURCE)},
              "passes": passes, "wrist_parameters": [round(float(v), 7) for v in wrist], "solves": solves,
              "final_objective": final_cost, "final_contact_cost": final_contact_cost, "final_collision": final_collision,
              "renders": renders, "output": {"path": str(OUTPUT.relative_to(ROOT))}}
    scene["V260_STATUS"] = "JOINT_COLLISION_SOLVE_VISUAL_REVIEW_REQUIRED"
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record["output"]["sha256"] = sha256(OUTPUT)
    (AUDIT / "v260_joint_collision_solve.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("V260_JOINT_COLLISION_SOLVE_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
