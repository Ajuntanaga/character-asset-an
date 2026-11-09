"""Collision-aware V250 fretting solve against real V206 neck/string surfaces."""

from pathlib import Path
from mathutils import Vector
import bpy

ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
BASE_SCRIPT = ROOT / "pipeline" / "build_v253_surface_contact_fretting.py"
ns = {"__name__": "v253_surface_solver_library"}
exec(compile(BASE_SCRIPT.read_text(encoding="utf-8"), str(BASE_SCRIPT), "exec"), ns)
ns["STAGE"] = ROOT / "production_v258_collision_aware_fretting"
ns["OUTPUT"] = ns["STAGE"] / "Character_An_collision_aware_fretting_v258.blend"
ns["RENDERS"] = ns["STAGE"] / "renders"
ns["AUDIT"] = ns["STAGE"] / "audit"

PROXY_LOCAL = {
    "index": (0.3058091, 0.0041983, "S5", 9, 234),
    "middle": (0.3296208, -0.0042574, "S4", 10, 211),
    "ring": (0.3050833, 0.0209915, "S7", 9, 14),
    "pinky": (0.3488616, 0.0301914, "S8", 11, 225),
}


def string_z(obj, x):
    points = [Vector(p.co[:3]) for spline in obj.data.splines for p in spline.points]
    for a, b in zip(points, points[1:]):
        if min(a.x, b.x) <= x <= max(a.x, b.x):
            return a.z + (x - a.x) / (b.x - a.x) * (b.z - a.z)
    return min(points, key=lambda p: abs(p.x - x)).z


def collision_depth(local: Vector, radius=0.006) -> float:
    """Depth inside an expanded neck solid; zero means collision-free."""
    if not -0.031 - radius <= local.x <= 0.605 + radius:
        return 0.0
    t = max(0.0, min(1.0, (local.x + 0.031) / 0.636))
    half_width = (0.033 + (0.0475 - 0.033) * t) + radius
    lo_z, hi_z = -0.027 - radius, 0.0155 + radius
    if abs(local.y) >= half_width or local.z <= lo_z or local.z >= hi_z:
        return 0.0
    return min(half_width - abs(local.y), local.z - lo_z, hi_z - local.z)


def solve_collision(armature, hand, digit, vertex, target):
    bones = [armature.pose.bones[f"{digit}_{j:02d}"] for j in range(1, 4)]
    for bone in bones:
        bone.rotation_mode = "XYZ"
        bone.rotation_euler = (0.10, 0.0, 0.0)
    parameters = [
        (bones[0], 0, -0.35, 0.90), (bones[0], 1, -0.75, 0.75),
        (bones[0], 2, -0.60, 0.60), (bones[1], 0, -0.05, 1.35),
        (bones[2], 0, -0.05, 1.05),
    ]
    neck_inv = bpy.data.objects["V206_NECK"].matrix_world.inverted()

    def objective():
        pad = ns["surface_world"](hand, vertex)
        cost = (pad - target).length_squared
        collision = 0.0
        for bone in bones:
            head = armature.matrix_world @ bone.head
            tail = armature.matrix_world @ bone.tail
            for fraction in (0.0, 0.25, 0.5, 0.75, 1.0):
                local = neck_inv @ head.lerp(tail, fraction)
                depth = collision_depth(local)
                collision += depth * depth
        # Collision dominates millimeter-scale contact gains.
        return cost + collision * 80.0, pad, collision

    bpy.context.view_layer.update()
    best, point, coll = objective(); evaluations = 1
    for step in (0.34, 0.18, 0.095, 0.05, 0.026, 0.013, 0.0065, 0.0032, 0.0016):
        for _ in range(6):
            improved = False
            for bone, axis, lower, upper in parameters:
                base = float(bone.rotation_euler[axis]); value = base; value_cost = best; value_point = point; value_coll = coll
                for candidate in (base - step, base + step):
                    if not lower <= candidate <= upper:
                        continue
                    bone.rotation_euler[axis] = candidate; bpy.context.view_layer.update()
                    cost, candidate_point, candidate_coll = objective(); evaluations += 1
                    if cost < value_cost:
                        value, value_cost, value_point, value_coll = candidate, cost, candidate_point, candidate_coll
                bone.rotation_euler[axis] = value; bpy.context.view_layer.update()
                if value_cost + 1e-14 < best:
                    best, point, coll, improved = value_cost, value_point, value_coll, True
            if not improved:
                break
    point = ns["surface_world"](hand, vertex)
    for bone in bones:
        bone.keyframe_insert(data_path="rotation_euler", frame=1, group=bone.name)
    return {
        "surface_vertex": vertex,
        "target_world_m": [round(float(v), 7) for v in target],
        "surface_world_m": [round(float(v), 7) for v in point],
        "surface_error_m": round((point-target).length, 7),
        "collision_penalty": round(coll, 10),
        "evaluations": evaluations,
        "rotations_xyz_rad": {b.name: [round(float(v), 6) for v in b.rotation_euler] for b in bones},
    }


def configure():
    neck = bpy.data.objects["V206_NECK"]
    contacts = {}
    for digit, (x, y, string, fret, vertex) in PROXY_LOCAL.items():
        curve = bpy.data.objects[f"V206_STRING_{string}"]
        z = string_z(curve, x) - 0.00185 + float(curve.data.bevel_depth)
        contacts[digit] = (vertex, neck.matrix_world @ Vector((x, y, z)), string, fret)
    ns["CONTACTS"] = contacts
    ns["THUMB"] = (286, neck.matrix_world @ Vector((0.3425739, 0.0034927, -0.027)))
    ns["solve_surface"] = solve_collision


if __name__ == "__main__":
    configure()
    ns["main"]()
