"""Add driven eyelid surfaces and mouth cavity to the V276 facial foundation."""

from pathlib import Path
import hashlib, json, math, bpy
from mathutils import Vector

ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v276_facial_shape_system" / "Character_An_facial_shapes_v276.blend"
STAGE = ROOT / "production_v276b_eyelids_mouth"
OUTPUT = STAGE / "Character_An_eyelids_mouth_v276b.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"
HEAD = "V216_REFERENCE_FITTED_HEAD"
RIG = "V239_CLEAN_CHARACTER_RIG"


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1048576), b""):
            digest.update(block)
    return digest.hexdigest()


def point_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def simple_material(name, color, roughness):
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = roughness
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.28
    return material


def bone_parent(obj):
    world = obj.matrix_world.copy()
    obj.parent = bpy.data.objects[RIG]
    obj.parent_type = "BONE"
    obj.parent_bone = "head"
    obj.matrix_world = world


def radial_patch(name, center, rx, rz, rings, segments, collection, material, neutral_builder, active_builder):
    verts = [neutral_builder(0.0, 0.0, center, rx, rz)]
    for ring in range(1, rings + 1):
        radius = ring / rings
        for index in range(segments):
            angle = 2 * math.pi * index / segments
            verts.append(neutral_builder(radius, angle, center, rx, rz))
    faces = []
    for index in range(segments):
        faces.append((0, 1 + index, 1 + (index + 1) % segments))
    for ring in range(1, rings):
        inner = 1 + (ring - 1) * segments
        outer = 1 + ring * segments
        for index in range(segments):
            nxt = (index + 1) % segments
            faces.append((inner + index, outer + index, outer + nxt, inner + nxt))
    mesh = bpy.data.meshes.new(name + "_MESH")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    mesh.materials.append(material)
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    basis = obj.shape_key_add(name="Basis", from_mix=False)
    active = obj.shape_key_add(name="Active", from_mix=False)
    active.data[0].co = active_builder(0.0, 0.0, center, rx, rz)
    vertex_index = 1
    for ring in range(1, rings + 1):
        radius = ring / rings
        for index in range(segments):
            angle = 2 * math.pi * index / segments
            active.data[vertex_index].co = active_builder(radius, angle, center, rx, rz)
            vertex_index += 1
    active.value = 0.0
    active.slider_min = 0.0
    active.slider_max = 1.0
    return obj


def lid_neutral(radius, angle, center, rx, rz):
    # Collapsed behind the eyeball along the upper lid rim.
    x = center.x + rx * radius * math.cos(angle)
    z = center.z + rz * (0.92 + 0.04 * radius * math.sin(angle))
    return (x, -0.106, z)


def lid_closed(radius, angle, center, rx, rz):
    x = center.x + rx * radius * math.cos(angle)
    z = center.z + rz * radius * math.sin(angle)
    normalized = min(0.98, (x - center.x) ** 2 / rx ** 2 + (z - center.z) ** 2 / rz ** 2)
    y = -0.1165 - 0.0025 * math.sqrt(max(0.0, 1.0 - normalized))
    return (x, y, z)


def mouth_neutral(radius, angle, center, rx, rz):
    return (center.x + 0.25 * rx * radius * math.cos(angle), -0.132, center.z)


def mouth_open(radius, angle, center, rx, rz):
    x = center.x + rx * radius * math.cos(angle)
    z = center.z + rz * radius * math.sin(angle)
    return (x, -0.1545, z)


def drive_shape(owner, key, property_name):
    driver = key.driver_add("value").driver
    driver.type = "SCRIPTED"
    variable = driver.variables.new()
    variable.name = "control"
    variable.type = "SINGLE_PROP"
    variable.targets[0].id = owner
    variable.targets[0].data_path = f'["{property_name}"]'
    driver.expression = "control"


def add_head_controls(head):
    controls = ("CTRL_JawOpen", "CTRL_Smile", "CTRL_BrowRaise", "CTRL_Blink_L", "CTRL_Blink_R")
    for name in controls:
        head[name] = 0.0
        ui = head.id_properties_ui(name)
        ui.update(min=0.0, max=1.0, soft_min=0.0, soft_max=1.0, description=f"V276b animator control: {name}")
    shape_keys = head.data.shape_keys
    if shape_keys.animation_data:
        shape_keys.animation_data_clear()
    for name in ("CTRL_JawOpen", "CTRL_Smile", "CTRL_BrowRaise"):
        key = shape_keys.key_blocks.get(name)
        if key:
            drive_shape(head, key, name)
    return controls


def main():
    if Path(bpy.data.filepath).resolve() != SOURCE.resolve():
        raise RuntimeError(f"Open V276 first: {SOURCE}")
    STAGE.mkdir(parents=True, exist_ok=True)
    RENDERS.mkdir(parents=True, exist_ok=True)
    AUDIT.mkdir(parents=True, exist_ok=True)
    head = bpy.data.objects[HEAD]
    controls = add_head_controls(head)
    collection = bpy.data.collections.get("V276B_FACE_ANATOMY") or bpy.data.collections.new("V276B_FACE_ANATOMY")
    if collection.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(collection)
    skin = simple_material("MAT_V276B_EYELID_SKIN", (0.12, 0.034, 0.012, 1), 0.50)
    cavity = simple_material("MAT_V276B_MOUTH_CAVITY", (0.002, 0.0002, 0.0002, 1), 0.68)
    pieces = []
    for side, x in (("L", 0.035), ("R", -0.035)):
        lid = radial_patch(
            f"V276B_EYELID_{side}", Vector((x, -0.115, 1.662)), 0.0165, 0.0080,
            5, 28, collection, skin, lid_neutral, lid_closed,
        )
        bone_parent(lid)
        drive_shape(head, lid.data.shape_keys.key_blocks["Active"], f"CTRL_Blink_{side}")
        pieces.append(lid)
    mouth = radial_patch(
        "V276B_MOUTH_CAVITY", Vector((0.0, -0.150, 1.579)), 0.026, 0.006,
        5, 32, collection, cavity, mouth_neutral, mouth_open,
    )
    bone_parent(mouth)
    drive_shape(head, mouth.data.shape_keys.key_blocks["Active"], "CTRL_JawOpen")
    pieces.append(mouth)

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
    tests = {
        "neutral": {},
        "blink": {"CTRL_Blink_L": 1.0, "CTRL_Blink_R": 1.0},
        "left_blink": {"CTRL_Blink_L": 1.0},
        "jaw_open": {"CTRL_JawOpen": 0.78},
        "smile": {"CTRL_Smile": 0.78, "CTRL_BrowRaise": 0.10},
    }
    renders = {}
    for label, values in tests.items():
        for control in controls:
            head[control] = values.get(control, 0.0)
        bpy.context.view_layer.update()
        path = RENDERS / f"v276b_{label}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        renders[label] = {"path": str(path.relative_to(ROOT)), "sha256": sha(path), "values": values}
    for obj in guitar:
        obj.hide_render = guitar_state[obj.name]
    for control in controls:
        head[control] = 0.0

    # Key custom properties so all driven anatomy follows one animator-facing channel per control.
    if head.animation_data:
        head.animation_data_clear()
    sequence = [(1, {}), (10, tests["blink"]), (20, tests["jaw_open"]), (30, tests["smile"]), (40, {})]
    for frame, values in sequence:
        for control in controls:
            head[control] = values.get(control, 0.0)
            head.keyframe_insert(data_path=f'["{control}"]', frame=frame)
    scene.frame_start, scene.frame_end = 1, 40
    scene.frame_set(1)
    record = {
        "schema": "v276b-eyelids-mouth-v1",
        "status": "BUILT_VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)},
        "controls": list(controls),
        "driven_pieces": [obj.name for obj in pieces],
        "proof_frames": [frame for frame, _ in sequence],
        "renders": renders,
        "output": {"path": str(OUTPUT.relative_to(ROOT))},
    }
    scene["V276B_STATUS"] = "DRIVEN_EYELIDS_MOUTH_VISUAL_REVIEW_REQUIRED"
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record["output"]["sha256"] = sha(OUTPUT)
    (AUDIT / "v276b_eyelids_mouth.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V276B_EYELIDS_MOUTH_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
