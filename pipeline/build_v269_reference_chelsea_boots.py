"""Build reference-proportioned Chelsea boots from the clean V265 inspection scene."""

from pathlib import Path
import hashlib, json, math, bpy
from mathutils import Vector

ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v265_neutral_wardrobe_inspection" / "Character_An_neutral_wardrobe_inspection_v265.blend"
STAGE = ROOT / "production_v269_reference_chelsea_boots"
OUTPUT = STAGE / "Character_An_reference_chelsea_boots_v269.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"
RIG = "V239_CLEAN_CHARACTER_RIG"


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1048576), b""):
            h.update(block)
    return h.hexdigest()


def point_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def material(name, color, roughness, metallic=0.0):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.32
    return mat


def parent_to_foot(obj, bone):
    world = obj.matrix_world.copy()
    obj.parent = bpy.data.objects[RIG]
    obj.parent_type = "BONE"
    obj.parent_bone = bone
    obj.matrix_world = world


def mesh_object(name, verts, faces, collection, mat, subdiv=1, bevel=0.0018):
    mesh = bpy.data.meshes.new(name + "_MESH")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    mesh.materials.append(mat)
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    if subdiv:
        mod = obj.modifiers.new(name + "_SUBDIV", "SUBSURF")
        mod.levels = 1
        mod.render_levels = 2
    edge = obj.modifiers.new(name + "_EDGE", "BEVEL")
    edge.width = bevel
    edge.segments = 3
    return obj


def cross_section(cx, y, half_width, bottom, top):
    # A slightly squared leather last: flat sole edge, sloping quarters, soft crown.
    shape = [
        (-0.78, 0.00), (-1.00, 0.16), (-0.98, 0.50), (-0.70, 0.82),
        (0.00, 1.00), (0.70, 0.82), (0.98, 0.50), (1.00, 0.16), (0.78, 0.00),
    ]
    return [(cx + sx * half_width, y, bottom + sz * (top - bottom)) for sx, sz in shape]


def loft_upper(name, cx, collection, leather):
    # y runs toe (-) to heel (+). Measurements follow the reference silhouette.
    sections = [
        (-0.176, 0.043, 0.038, 0.079),
        (-0.150, 0.059, 0.037, 0.090),
        (-0.095, 0.064, 0.037, 0.104),
        (-0.030, 0.061, 0.037, 0.126),
        (0.030, 0.057, 0.037, 0.151),
        (0.082, 0.053, 0.037, 0.159),
        (0.112, 0.050, 0.041, 0.146),
    ]
    ring = 9
    verts = []
    for y, width, bottom, top in sections:
        verts.extend(cross_section(cx, y, width, bottom, top))
    faces = []
    for row in range(len(sections) - 1):
        for i in range(ring):
            j = (i + 1) % ring
            faces.append((row * ring + i, row * ring + j, (row + 1) * ring + j, (row + 1) * ring + i))
    faces.extend((tuple(range(ring - 1, -1, -1)), tuple((len(sections) - 1) * ring + i for i in range(ring))))
    return mesh_object(name, verts, faces, collection, leather, 1, 0.0015)


def loft_shaft(name, cx, collection, leather):
    rings = [
        (0.118, 0.052, 0.056, 0.020),
        (0.165, 0.053, 0.054, 0.024),
        (0.225, 0.054, 0.052, 0.028),
        (0.282, 0.055, 0.051, 0.031),
    ]
    seg = 20
    verts = []
    for z, rx, ry, cy in rings:
        for i in range(seg):
            a = 2.0 * math.pi * i / seg
            verts.append((cx + rx * math.cos(a), cy + ry * math.sin(a), z))
    faces = []
    for row in range(len(rings) - 1):
        for i in range(seg):
            j = (i + 1) % seg
            faces.append((row * seg + i, row * seg + j, (row + 1) * seg + j, (row + 1) * seg + i))
    return mesh_object(name, verts, faces, collection, leather, 1, 0.0015)


def rounded_cube(name, location, dimensions, collection, mat, bevel):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    for old_collection in tuple(obj.users_collection):
        old_collection.objects.unlink(obj)
    collection.objects.link(obj)
    obj.dimensions = dimensions
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    mod = obj.modifiers.new(name + "_BEVEL", "BEVEL")
    mod.width = bevel
    mod.segments = 4
    return obj


def main():
    if Path(bpy.data.filepath).resolve() != SOURCE.resolve():
        raise RuntimeError(f"Open V265 first: {SOURCE}")
    STAGE.mkdir(parents=True, exist_ok=True)
    RENDERS.mkdir(parents=True, exist_ok=True)
    AUDIT.mkdir(parents=True, exist_ok=True)

    hidden = []
    for obj in bpy.context.scene.objects:
        if obj.name.startswith("V243_BOOT_") or obj.name.startswith("V268_BOOT_"):
            obj.hide_render = True
            obj.hide_viewport = True
            hidden.append(obj.name)

    collection = bpy.data.collections.get("V269_REFERENCE_CHELSEA_BOOTS") or bpy.data.collections.new("V269_REFERENCE_CHELSEA_BOOTS")
    if collection.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(collection)

    leather = material("MAT_V269_BURNISHED_COGNAC", (0.105, 0.027, 0.010, 1), 0.31)
    welt = material("MAT_V269_DARK_WELT", (0.018, 0.008, 0.004, 1), 0.52)
    sole = material("MAT_V269_SOLE", (0.008, 0.006, 0.005, 1), 0.68)
    gore = material("MAT_V269_GORE", (0.008, 0.009, 0.009, 1), 0.9)
    pieces = []

    for side, cx in (("L", -0.165), ("R", 0.165)):
        foot = loft_upper(f"V269_BOOT_UPPER_{side}", cx, collection, leather)
        shaft = loft_shaft(f"V269_BOOT_SHAFT_{side}", cx, collection, leather)
        welt_obj = rounded_cube(f"V269_BOOT_WELT_{side}", (cx, -0.032, 0.034), (0.132, 0.306, 0.012), collection, welt, 0.004)
        sole_obj = rounded_cube(f"V269_BOOT_SOLE_{side}", (cx, -0.032, 0.025), (0.128, 0.300, 0.014), collection, sole, 0.004)
        heel = rounded_cube(f"V269_BOOT_HEEL_{side}", (cx, 0.078, 0.037), (0.105, 0.071, 0.034), collection, sole, 0.004)
        sign = -1 if side == "L" else 1
        outer = rounded_cube(f"V269_BOOT_GORE_OUTER_{side}", (cx + sign * 0.054, 0.024, 0.220), (0.0035, 0.074, 0.082), collection, gore, 0.002)
        inner = rounded_cube(f"V269_BOOT_GORE_INNER_{side}", (cx - sign * 0.054, 0.024, 0.220), (0.0035, 0.074, 0.082), collection, gore, 0.002)
        tab = rounded_cube(f"V269_BOOT_PULL_TAB_{side}", (cx, 0.080, 0.296), (0.017, 0.007, 0.039), collection, leather, 0.002)
        for obj in (foot, shaft, welt_obj, sole_obj, heel, outer, inner, tab):
            parent_to_foot(obj, f"foot_fk.{side}")
            pieces.append(obj)

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.look = "AgX - Medium High Contrast"
    cam = bpy.data.objects["CAM_V211_FRONT"]
    rig = bpy.data.objects[RIG]
    hand_rig = bpy.data.objects["V250_FRETTING_HAND_RIG"]
    old_rig_state, old_hand_state = rig.data.pose_position, hand_rig.data.pose_position
    guitar = [obj for obj in scene.objects if obj.name.startswith("V206_")]
    guitar_state = {obj.name: (obj.hide_render, obj.hide_viewport) for obj in guitar}
    rig.data.pose_position = "REST"
    hand_rig.data.pose_position = "REST"
    for obj in guitar:
        obj.hide_render = True
        obj.hide_viewport = True
    bpy.context.view_layer.update()

    views = {
        "boots_front": (Vector((0, -1.38, 0.22)), Vector((0, -0.03, 0.15)), 92, (1100, 800)),
        "boots_three_quarter": (Vector((-0.64, -1.16, 0.28)), Vector((0, -0.03, 0.15)), 92, (1100, 800)),
        "boots_profile": (Vector((-1.18, -0.02, 0.25)), Vector((0, -0.03, 0.15)), 92, (1100, 800)),
        "full_front": (Vector((0, -3.65, 1.02)), Vector((0, 0, 1.02)), 72, (900, 1100)),
    }
    renders = {}
    for label, (location, target, lens, resolution) in views.items():
        cam.location = location
        cam.data.lens = lens
        point_at(cam, target)
        scene.camera = cam
        scene.render.resolution_x, scene.render.resolution_y = resolution
        scene.render.resolution_percentage = 100
        path = RENDERS / f"v269_{label}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        renders[label] = {"path": str(path.relative_to(ROOT)), "sha256": sha(path)}

    rig.data.pose_position, hand_rig.data.pose_position = old_rig_state, old_hand_state
    for obj in guitar:
        obj.hide_render, obj.hide_viewport = guitar_state[obj.name]
    bpy.context.view_layer.update()
    record = {
        "schema": "v269-reference-chelsea-boots-v1",
        "status": "BUILT_VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)},
        "hidden_old_boots": hidden,
        "reference_images": ["Focused guitarist character model sheet.png", "Watercolor character turnaround sheet.png"],
        "pieces": [obj.name for obj in pieces],
        "renders": renders,
        "output": {"path": str(OUTPUT.relative_to(ROOT))},
    }
    scene["V269_STATUS"] = "REFERENCE_CHELSEA_BOOTS_VISUAL_REVIEW_REQUIRED"
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record["output"]["sha256"] = sha(OUTPUT)
    (AUDIT / "v269_reference_chelsea_boots.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V269_REFERENCE_CHELSEA_BOOTS_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
