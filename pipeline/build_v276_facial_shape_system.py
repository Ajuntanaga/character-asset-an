"""Add animator-facing facial shape keys and expression proof renders."""

from pathlib import Path
import hashlib, json, math, bpy
from mathutils import Vector

ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v270_boot_finish_cuffs" / "Character_An_boot_finish_cuffs_v270.blend"
STAGE = ROOT / "production_v276_facial_shape_system"
OUTPUT = STAGE / "Character_An_facial_shapes_v276.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"
HEAD = "V216_REFERENCE_FITTED_HEAD"


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1048576), b""):
            h.update(block)
    return h.hexdigest()


def point_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def smoothstep(edge0, edge1, value):
    if edge0 == edge1:
        return 0.0
    t = max(0.0, min(1.0, (value - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def gaussian(value, center, radius):
    return math.exp(-((value - center) / max(radius, 1e-6)) ** 2)


def add_shape(head, name, displacement):
    key = head.shape_key_add(name=name, from_mix=False)
    inverse = head.matrix_world.inverted().to_3x3()
    moved = 0
    maximum = 0.0
    for vertex, point in zip(head.data.vertices, key.data):
        world = head.matrix_world @ vertex.co
        delta_world = displacement(world)
        if delta_world.length > 1e-7:
            point.co += inverse @ delta_world
            moved += 1
            maximum = max(maximum, delta_world.length)
    key.value = 0.0
    key.slider_min = 0.0
    key.slider_max = 1.0
    return {"name": name, "moved_vertices": moved, "max_displacement_m": maximum}


def jaw_open(p):
    front = smoothstep(-0.03, -0.115, p.y)
    lower = smoothstep(1.585, 1.455, p.z) * smoothstep(1.385, 1.455, p.z)
    center = 1.0 - smoothstep(0.085, 0.125, abs(p.x))
    w = front * lower * center
    return Vector((0.0, 0.008 * w, -0.030 * w))


def smile(p):
    front = smoothstep(-0.07, -0.125, p.y)
    vertical = gaussian(p.z, 1.565, 0.035)
    side = smoothstep(0.018, 0.075, abs(p.x)) * (1.0 - smoothstep(0.075, 0.115, abs(p.x)))
    w = front * vertical * side
    return Vector(((0.014 if p.x >= 0 else -0.014) * w, -0.0015 * w, 0.010 * w))


def brow_raise(p):
    front = smoothstep(-0.055, -0.095, p.y)
    vertical = gaussian(p.z, 1.716, 0.025)
    lateral = (1.0 - smoothstep(0.100, 0.130, abs(p.x))) * smoothstep(0.012, 0.030, abs(p.x))
    w = front * vertical * lateral
    return Vector((0.0, -0.001 * w, 0.014 * w))


def blink(side):
    cx = 0.035 if side == "L" else -0.035

    def deform(p):
        front = smoothstep(-0.096, -0.116, p.y)
        lateral = gaussian(p.x, cx, 0.023)
        vertical = gaussian(p.z, 1.674, 0.017)
        w = front * lateral * vertical
        dz = (1.6715 - p.z) * 0.94 * w
        return Vector((0.0, -0.0006 * w, dz))

    return deform


def main():
    if Path(bpy.data.filepath).resolve() != SOURCE.resolve():
        raise RuntimeError(f"Open V270 first: {SOURCE}")
    STAGE.mkdir(parents=True, exist_ok=True)
    RENDERS.mkdir(parents=True, exist_ok=True)
    AUDIT.mkdir(parents=True, exist_ok=True)
    head = bpy.data.objects[HEAD]
    if head.data.shape_keys:
        head.shape_key_clear()
        while head.data.shape_keys and len(head.data.shape_keys.key_blocks) > 0:
            head.shape_key_remove(head.data.shape_keys.key_blocks[-1])
    head.shape_key_add(name="Basis", from_mix=False)
    records = [
        add_shape(head, "CTRL_JawOpen", jaw_open),
        add_shape(head, "CTRL_Smile", smile),
        add_shape(head, "CTRL_BrowRaise", brow_raise),
    ]
    head["facial_control_schema"] = "V276_FACS_FOUNDATION_V1"
    head["facial_control_notes"] = "Non-destructive foundation keys; corrective sculpt pass required after identity review."

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.look = "AgX - Medium High Contrast"
    cam = bpy.data.objects["CAM_V211_FRONT"]
    cam.location = Vector((0.0, -2.18, 1.655))
    cam.data.lens = 92
    point_at(cam, Vector((0.0, -0.015, 1.645)))
    scene.camera = cam
    scene.render.resolution_x = 800
    scene.render.resolution_y = 800
    scene.render.resolution_percentage = 100
    guitar = [obj for obj in scene.objects if obj.name.startswith("V206_")]
    guitar_state = {obj.name: obj.hide_render for obj in guitar}
    for obj in guitar:
        obj.hide_render = True
    keys = head.data.shape_keys.key_blocks
    tests = {
        "neutral": {},
        "jaw_open": {"CTRL_JawOpen": 0.72},
        "smile": {"CTRL_Smile": 0.78, "CTRL_BrowRaise": 0.12},
        "brow_raise": {"CTRL_BrowRaise": 0.85},
    }
    renders = {}
    for label, values in tests.items():
        for key in keys:
            if key.name != "Basis":
                key.value = values.get(key.name, 0.0)
        bpy.context.view_layer.update()
        path = RENDERS / f"v276_{label}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        renders[label] = {"path": str(path.relative_to(ROOT)), "sha256": sha(path), "values": values}
    for obj in guitar:
        obj.hide_render = guitar_state[obj.name]
    for key in keys:
        if key.name != "Basis":
            key.value = 0.0

    # Key the proof sequence while leaving frame 1 neutral.
    scene.frame_start, scene.frame_end = 1, 50
    sequence = [(1, {}), (10, tests["jaw_open"]), (20, tests["smile"]), (30, tests["brow_raise"]), (40, {})]
    for frame, values in sequence:
        for key in keys:
            if key.name == "Basis":
                continue
            key.value = values.get(key.name, 0.0)
            key.keyframe_insert(data_path="value", frame=frame)
    scene.frame_set(1)
    record = {
        "schema": "v276-facial-shape-system-v1",
        "status": "PARTIAL_FOUNDATION_JAW_SMILE_BROW_BLINK_REJECTED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)},
        "head": HEAD,
        "controls": records,
        "proof_frames": [frame for frame, _ in sequence],
        "renders": renders,
        "output": {"path": str(OUTPUT.relative_to(ROOT))},
    }
    scene["V276_STATUS"] = "FACIAL_SHAPE_FOUNDATION_VISUAL_REVIEW_REQUIRED"
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record["output"]["sha256"] = sha(OUTPUT)
    (AUDIT / "v276_facial_shapes.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V276_FACIAL_SHAPES_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
