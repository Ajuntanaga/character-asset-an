"""Build texture-matched driven eyelid patches from the visible head topology."""

from pathlib import Path
import hashlib, json, math, bpy
from mathutils import Vector

ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v276_facial_shape_system" / "Character_An_facial_shapes_v276.blend"
STAGE = ROOT / "production_v276c_texture_matched_lids"
OUTPUT = STAGE / "Character_An_texture_matched_lids_v276c.blend"
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
    return material


def bone_parent(obj):
    world = obj.matrix_world.copy()
    obj.parent = bpy.data.objects[RIG]
    obj.parent_type = "BONE"
    obj.parent_bone = "head"
    obj.matrix_world = world


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
        head.id_properties_ui(name).update(min=0.0, max=1.0, soft_min=0.0, soft_max=1.0)
    shape_keys = head.data.shape_keys
    if shape_keys.animation_data:
        shape_keys.animation_data_clear()
    for name in ("CTRL_JawOpen", "CTRL_Smile", "CTRL_BrowRaise"):
        key = shape_keys.key_blocks.get(name)
        if key:
            drive_shape(head, key, name)
    return controls


def extract_lid_patch(head, side, cx, collection):
    source_mesh = head.data
    world = head.matrix_world
    selected = []
    for polygon in source_mesh.polygons:
        points = [world @ source_mesh.vertices[index].co for index in polygon.vertices]
        if all(abs(point.x - cx) <= 0.026 and 1.646 <= point.z <= 1.687 and point.y <= -0.090 for point in points):
            selected.append(polygon)
    vertex_map = {}
    source_indices = []
    vertices = []
    faces = []
    for polygon in selected:
        face = []
        for source_index in polygon.vertices:
            if source_index not in vertex_map:
                vertex_map[source_index] = len(vertices)
                source_indices.append(source_index)
                point = world @ source_mesh.vertices[source_index].co
                vertices.append((point.x, point.y + 0.0022, point.z))
            face.append(vertex_map[source_index])
        faces.append(tuple(face))
    if not faces:
        raise RuntimeError(f"No eyelid faces selected for {side}")
    mesh = bpy.data.meshes.new(f"V276C_EYELID_{side}_MESH")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(f"V276C_EYELID_{side}", mesh)
    collection.objects.link(obj)
    mesh.materials.append(head.material_slots[0].material)
    # Preserve the packed identity texture through exact loop UV transfer.
    if source_mesh.uv_layers.active:
        uv_layer = mesh.uv_layers.new(name=source_mesh.uv_layers.active.name)
        for new_polygon, source_polygon in zip(mesh.polygons, selected):
            for offset in range(source_polygon.loop_total):
                uv_layer.data[new_polygon.loop_start + offset].uv = source_mesh.uv_layers.active.data[source_polygon.loop_start + offset].uv
    obj.shape_key_add(name="Basis", from_mix=False)
    blink = obj.shape_key_add(name="Blink", from_mix=False)
    seam_z = 1.662
    for new_index, source_index in enumerate(source_indices):
        point = world @ source_mesh.vertices[source_index].co
        wx = max(0.0, 1.0 - abs(point.x - cx) / 0.026)
        wz = max(0.0, 1.0 - abs(point.z - seam_z) / 0.025)
        weight = (wx * wz) ** 0.55
        blink.data[new_index].co = (
            point.x,
            point.y - 0.0018 * weight,
            point.z + (seam_z - point.z) * 0.97 * weight,
        )
    blink.value = 0.0
    blink.slider_min = 0.0
    blink.slider_max = 1.0
    bone_parent(obj)
    drive_shape(head, blink, f"CTRL_Blink_{side}")
    return obj, {"faces": len(faces), "vertices": len(vertices)}


def radial_mouth(collection, material):
    rings, segments = 5, 32
    center = Vector((0.0, -0.150, 1.579))
    rx, rz = 0.026, 0.006
    vertices = [(center.x, -0.132, center.z)]
    for ring in range(1, rings + 1):
        radius = ring / rings
        for index in range(segments):
            angle = 2 * math.pi * index / segments
            vertices.append((center.x + 0.25 * rx * radius * math.cos(angle), -0.132, center.z))
    faces = []
    for index in range(segments):
        faces.append((0, 1 + index, 1 + (index + 1) % segments))
    for ring in range(1, rings):
        inner, outer = 1 + (ring - 1) * segments, 1 + ring * segments
        for index in range(segments):
            nxt = (index + 1) % segments
            faces.append((inner + index, outer + index, outer + nxt, inner + nxt))
    mesh = bpy.data.meshes.new("V276C_MOUTH_CAVITY_MESH")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new("V276C_MOUTH_CAVITY", mesh)
    collection.objects.link(obj)
    mesh.materials.append(material)
    obj.shape_key_add(name="Basis", from_mix=False)
    active = obj.shape_key_add(name="Open", from_mix=False)
    active.data[0].co = (center.x, -0.1545, center.z)
    vertex_index = 1
    for ring in range(1, rings + 1):
        radius = ring / rings
        for index in range(segments):
            angle = 2 * math.pi * index / segments
            active.data[vertex_index].co = (center.x + rx * radius * math.cos(angle), -0.1545, center.z + rz * radius * math.sin(angle))
            vertex_index += 1
    bone_parent(obj)
    return obj, active


def main():
    if Path(bpy.data.filepath).resolve() != SOURCE.resolve():
        raise RuntimeError(f"Open V276 first: {SOURCE}")
    STAGE.mkdir(parents=True, exist_ok=True)
    RENDERS.mkdir(parents=True, exist_ok=True)
    AUDIT.mkdir(parents=True, exist_ok=True)
    head = bpy.data.objects[HEAD]
    controls = add_head_controls(head)
    collection = bpy.data.collections.get("V276C_FACE_ANATOMY") or bpy.data.collections.new("V276C_FACE_ANATOMY")
    if collection.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(collection)
    pieces, topology = [], {}
    for side, cx in (("L", 0.035), ("R", -0.035)):
        lid, stats = extract_lid_patch(head, side, cx, collection)
        pieces.append(lid)
        topology[lid.name] = stats
    cavity_material = simple_material("MAT_V276C_MOUTH_CAVITY", (0.001, 0.0001, 0.0001, 1), 0.70)
    mouth, mouth_key = radial_mouth(collection, cavity_material)
    drive_shape(head, mouth_key, "CTRL_JawOpen")
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
        path = RENDERS / f"v276c_{label}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        renders[label] = {"path": str(path.relative_to(ROOT)), "sha256": sha(path), "values": values}
    for obj in guitar:
        obj.hide_render = guitar_state[obj.name]
    for control in controls:
        head[control] = 0.0
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
        "schema": "v276c-texture-matched-lids-v1",
        "status": "BUILT_VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)},
        "controls": list(controls),
        "pieces": [obj.name for obj in pieces],
        "topology": topology,
        "proof_frames": [frame for frame, _ in sequence],
        "renders": renders,
        "output": {"path": str(OUTPUT.relative_to(ROOT))},
    }
    scene["V276C_STATUS"] = "TEXTURE_MATCHED_LIDS_VISUAL_REVIEW_REQUIRED"
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record["output"]["sha256"] = sha(OUTPUT)
    (AUDIT / "v276c_texture_matched_lids.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V276C_TEXTURE_MATCHED_LIDS_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
