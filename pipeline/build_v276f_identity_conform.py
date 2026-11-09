"""Seat the jaw and conform animation topology toward the fitted identity."""

from pathlib import Path
import hashlib, json, math
import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v276e_head_hierarchy_jaw" / "Character_An_head_hierarchy_jaw_v276e.blend"
STAGE = ROOT / "production_v276f_identity_conform"
OUTPUT = STAGE / "Character_An_identity_conform_v276f.blend"
RENDERS, AUDIT = STAGE / "renders", STAGE / "audit"
HEAD = "V276E_GEO-head_animation_realistic"
TARGET = "V216_REFERENCE_FITTED_HEAD"
JAW = "V276E_Jaw - Realistic"


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            h.update(block)
    return h.hexdigest()


def smoothstep(a, b, value):
    t = max(0.0, min(1.0, (value - a) / (b - a)))
    return t * t * (3.0 - 2.0 * t)


def world_bounds(obj):
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    low = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
    high = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
    return low, high


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

    jaw_low, jaw_high = world_bounds(jaw)
    jaw_center = (jaw_low + jaw_high) * 0.5
    jaw_target = Vector((0.0, -0.045, 1.565))
    jaw_delta = jaw_target - jaw_center
    jaw.matrix_world = Matrix.Translation(jaw_delta) @ jaw.matrix_world
    jaw_low_after, jaw_high_after = world_bounds(jaw)

    if head.data.shape_keys:
        while head.data.shape_keys and len(head.data.shape_keys.key_blocks):
            head.shape_key_remove(head.data.shape_keys.key_blocks[-1])
    head.shape_key_add(name="Basis", from_mix=False)
    identity = head.shape_key_add(name="IDENTITY_V216_CONFORM", from_mix=False)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    tree = BVHTree.FromObject(target, depsgraph, deform=True, cage=False)
    inverse = head.matrix_world.inverted()
    target_inverse = target.matrix_world.inverted()
    distances = []
    moved = 0
    for vertex, point in zip(head.data.vertices, identity.data):
        world = head.matrix_world @ vertex.co
        nearest = tree.find_nearest(target_inverse @ world)
        if nearest is None:
            continue
        location_local, _normal, _face, _distance_local = nearest
        location = target.matrix_world @ location_local
        distance = (location - world).length
        neck_weight = smoothstep(1.405, 1.495, world.z)
        lateral_weight = 0.72 if abs(world.x) > 0.125 else 1.0
        scalp_weight = 0.82 if world.z > 1.755 else 1.0
        distance_weight = min(1.0, 0.035 / max(distance, 1e-9))
        weight = neck_weight * lateral_weight * scalp_weight * distance_weight
        destination = world.lerp(location, weight)
        point.co = inverse @ destination
        distances.append(distance)
        if (destination - world).length > 1e-6:
            moved += 1
    identity.value = 1.0

    scene = bpy.context.scene
    cam = bpy.data.objects["V276E_CAMERA"]
    candidate = [obj for obj in bpy.data.objects if obj.name.startswith("V276E_") and obj.type in {"MESH", "CURVE"}]
    eyes = [obj for obj in candidate if "iris" in obj.name.lower() or "sclera" in obj.name.lower()]
    target_state = target.hide_render
    candidate_state = {obj.name: obj.hide_render for obj in candidate}
    target.hide_render = False
    for obj in candidate:
        obj.hide_render = True
    cam.location = Vector((0.0, -2.05, 1.605))
    cam.rotation_euler = (Vector((0.0, -0.005, 1.605)) - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = 92
    target_path = RENDERS / "v276f_reference_target_front.png"
    render(scene, cam, target_path)

    target.hide_render = True
    for obj in candidate:
        obj.hide_render = False
    conformed_path = RENDERS / "v276f_conformed_front.png"
    render(scene, cam, conformed_path)
    cam.location = Vector((-1.15, -1.72, 1.606))
    cam.rotation_euler = (Vector((0.0, -0.005, 1.605)) - cam.location).to_track_quat("-Z", "Y").to_euler()
    three_quarter_path = RENDERS / "v276f_conformed_three_quarter.png"
    render(scene, cam, three_quarter_path)

    # Show the seated oral asset independently; it should no longer sit below
    # the neck, while remaining hidden behind the closed lips in beauty views.
    for obj in candidate:
        obj.hide_render = obj is not jaw
    cam.location = Vector((0.0, -1.25, 1.54))
    cam.rotation_euler = (Vector((0.0, -0.07, 1.54)) - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = 110
    jaw_path = RENDERS / "v276f_seated_jaw_front.png"
    render(scene, cam, jaw_path)

    target.hide_render = target_state
    for obj in candidate:
        obj.hide_render = candidate_state[obj.name]
    target.hide_render = True
    head.hide_render = False
    jaw.hide_render = False
    for obj in eyes:
        obj.hide_render = False
    scene["V276F_STATUS"] = "IDENTITY_CONFORM_VISUAL_REVIEW_REQUIRED"
    scene["V276F_JAW_TARGET"] = list(jaw_target)
    scene["V276F_IDENTITY_SHAPE"] = identity.name
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v276f-identity-conform-v1",
        "status": "BUILT_VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)},
        "head": HEAD,
        "target": TARGET,
        "shape_key": identity.name,
        "moved_vertices": moved,
        "nearest_distance_m": {
            "mean": sum(distances) / len(distances),
            "max": max(distances),
        },
        "jaw": {
            "object": JAW,
            "translation_m": list(jaw_delta),
            "bounds_after": [list(jaw_low_after), list(jaw_high_after)],
        },
        "renders": [str(path.relative_to(ROOT)) for path in (target_path, conformed_path, three_quarter_path, jaw_path)],
        "output": {"path": str(OUTPUT.relative_to(ROOT))},
    }
    record["output"]["sha256"] = sha(OUTPUT)
    (AUDIT / "v276f_identity_conform.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V276F_IDENTITY_CONFORM_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
