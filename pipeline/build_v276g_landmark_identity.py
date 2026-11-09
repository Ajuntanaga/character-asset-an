"""Conform the official animation head with a smooth semantic landmark warp."""

from pathlib import Path
import hashlib, json, math
import bpy
from mathutils import Matrix, Vector

ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v276e_head_hierarchy_jaw" / "Character_An_head_hierarchy_jaw_v276e.blend"
STAGE = ROOT / "production_v276g_landmark_identity"
OUTPUT = STAGE / "Character_An_landmark_identity_v276g.blend"
RENDERS, AUDIT = STAGE / "renders", STAGE / "audit"
HEAD, TARGET, JAW = "V276E_GEO-head_animation_realistic", "V216_REFERENCE_FITTED_HEAD", "V276E_Jaw - Realistic"


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            h.update(block)
    return h.hexdigest()


def smoothstep(a, b, value):
    t = max(0.0, min(1.0, (value - a) / (b - a)))
    return t * t * (3.0 - 2.0 * t)


def vertices_world(obj):
    return [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]


def front(points, x, z, rx, rz):
    candidates = [point for point in points if abs(point.x - x) <= rx and abs(point.z - z) <= rz]
    if not candidates:
        raise RuntimeError(f"No front landmark candidates x={x} z={z}")
    return min(candidates, key=lambda point: point.y)


def extreme(points, axis, mode, z0, z1):
    candidates = [point for point in points if z0 <= point.z <= z1]
    return (max if mode == "max" else min)(candidates, key=lambda point: point[axis])


def point_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(scene, cam, path):
    scene.camera = cam
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def main():
    if Path(bpy.data.filepath).resolve() != SOURCE.resolve():
        raise RuntimeError(f"Open V276E first: {SOURCE}")
    for folder in (STAGE, RENDERS, AUDIT):
        folder.mkdir(parents=True, exist_ok=True)
    head, target, jaw = (bpy.data.objects[name] for name in (HEAD, TARGET, JAW))
    source_points, target_points = vertices_world(head), vertices_world(target)
    specs = [
        ("nose_tip", 0.0, 1.635, 0.025, 0.045, 0.060),
        ("upper_lip", 0.0, 1.580, 0.025, 0.016, 0.050),
        ("lower_lip", 0.0, 1.555, 0.025, 0.016, 0.050),
        ("mouth_L", 0.045, 1.568, 0.018, 0.025, 0.052),
        ("mouth_R", -0.045, 1.568, 0.018, 0.025, 0.052),
        ("lid_L", 0.037, 1.676, 0.022, 0.020, 0.050),
        ("lid_R", -0.037, 1.676, 0.022, 0.020, 0.050),
        ("brow_L", 0.045, 1.718, 0.028, 0.022, 0.060),
        ("brow_R", -0.045, 1.718, 0.028, 0.022, 0.060),
        ("cheek_L", 0.088, 1.625, 0.025, 0.040, 0.072),
        ("cheek_R", -0.088, 1.625, 0.025, 0.040, 0.072),
        ("chin", 0.0, 1.505, 0.035, 0.035, 0.070),
        ("temple_L", 0.105, 1.700, 0.030, 0.045, 0.090),
        ("temple_R", -0.105, 1.700, 0.030, 0.045, 0.090),
    ]
    landmarks = []
    for name, x, z, rx, rz, radius in specs:
        src, dst = front(source_points, x, z, rx, rz), front(target_points, x, z, rx, rz)
        landmarks.append((name, src, dst, radius))
    for name, axis, mode, z0, z1, radius in (
        ("side_L", 0, "max", 1.59, 1.76, 0.12),
        ("side_R", 0, "min", 1.59, 1.76, 0.12),
        ("crown", 2, "max", 1.70, 1.82, 0.14),
        ("back_head", 1, "max", 1.58, 1.75, 0.14),
    ):
        landmarks.append((name, extreme(source_points, axis, mode, z0, z1), extreme(target_points, axis, mode, z0, z1), radius))

    def warp(world):
        weighted = Vector()
        total = 0.0
        for _name, src, dst, radius in landmarks:
            distance = (world - src).length
            weight = math.exp(-((distance / radius) ** 4))
            weighted += (dst - src) * weight
            total += weight
        if total < 1e-8:
            return world
        neck = smoothstep(1.405, 1.485, world.z)
        return world + weighted * (neck / total)

    if head.data.shape_keys:
        while head.data.shape_keys and len(head.data.shape_keys.key_blocks):
            head.shape_key_remove(head.data.shape_keys.key_blocks[-1])
    head.shape_key_add(name="Basis", from_mix=False)
    identity = head.shape_key_add(name="IDENTITY_LANDMARK_WARP", from_mix=False)
    inverse = head.matrix_world.inverted()
    displacements = []
    for vertex, point in zip(head.data.vertices, identity.data):
        world = head.matrix_world @ vertex.co
        destination = warp(world)
        point.co = inverse @ destination
        displacements.append((destination - world).length)
    identity.value = 1.0

    # Align the eye hierarchy roots to the already fitted V212/V216 eye centers.
    eye_moves = {}
    for side, desired_x in (("L", 0.035), ("R", -0.035)):
        sclera = bpy.data.objects[f"V276E_GEO-head_animation_realistic.sclera.{side}"]
        current = sclera.matrix_world.translation.copy()
        desired = Vector((desired_x, -0.100, 1.681))
        sclera.matrix_world = Matrix.Translation(desired - current) @ sclera.matrix_world
        eye_moves[side] = list(desired - current)

    # Seat the complete dental/jaw asset behind the closed lips.
    points = [jaw.matrix_world @ Vector(corner) for corner in jaw.bound_box]
    center = Vector(tuple((min(p[i] for p in points) + max(p[i] for p in points)) * 0.5 for i in range(3)))
    jaw_target = Vector((0.0, -0.045, 1.565))
    jaw.matrix_world = Matrix.Translation(jaw_target - center) @ jaw.matrix_world

    scene, cam = bpy.context.scene, bpy.data.objects["V276E_CAMERA"]
    candidate = [obj for obj in bpy.data.objects if obj.name.startswith("V276E_") and obj.type == "MESH"]
    cam.data.lens = 92
    views = {
        "front": (Vector((0.0, -2.05, 1.605)), Vector((0.0, -0.005, 1.605))),
        "three_quarter": (Vector((-1.15, -1.72, 1.606)), Vector((0.0, -0.005, 1.605))),
        "profile": (Vector((-2.05, 0.0, 1.605)), Vector((0.0, -0.005, 1.605))),
    }
    target.hide_render = True
    for obj in candidate:
        obj.hide_render = False
    renders = []
    for label, (location, look) in views.items():
        cam.location = location
        point_at(cam, look)
        path = RENDERS / f"v276g_{label}.png"
        render(scene, cam, path)
        renders.append(str(path.relative_to(ROOT)))
    scene["V276G_STATUS"] = "LANDMARK_IDENTITY_VISUAL_REVIEW_REQUIRED"
    scene["V276G_IDENTITY_SHAPE"] = identity.name
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    landmark_records = [
        {"name": name, "source": list(src), "target": list(dst), "delta_m": list(dst - src), "radius_m": radius}
        for name, src, dst, radius in landmarks
    ]
    record = {
        "schema": "v276g-landmark-identity-v1",
        "status": "BUILT_VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)},
        "shape_key": identity.name,
        "landmarks": landmark_records,
        "displacement_m": {"mean": sum(displacements) / len(displacements), "max": max(displacements)},
        "eye_moves_m": eye_moves,
        "jaw_target": list(jaw_target),
        "renders": renders,
        "output": {"path": str(OUTPUT.relative_to(ROOT))},
    }
    record["output"]["sha256"] = sha(OUTPUT)
    (AUDIT / "v276g_landmark_identity.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V276G_LANDMARK_IDENTITY_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
