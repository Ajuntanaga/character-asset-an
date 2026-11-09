"""Create an explicit open-front jacket shell and weighted sleeves from V270."""

from pathlib import Path
import hashlib, json, math, bpy
from mathutils import Vector

ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v270_boot_finish_cuffs" / "Character_An_boot_finish_cuffs_v270.blend"
STAGE = ROOT / "production_v271_explicit_jacket_topology"
OUTPUT = STAGE / "Character_An_explicit_jacket_v271.blend"
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


def jacket_material():
    mat = bpy.data.materials.get("MAT_V271_WASHED_BLACK_DENIM") or bpy.data.materials.new("MAT_V271_WASHED_BLACK_DENIM")
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (0.010, 0.012, 0.015, 1)
    bsdf.inputs["Roughness"].default_value = 0.76
    noise = nodes.get("V271_DENIM_BREAKUP") or nodes.new("ShaderNodeTexNoise")
    noise.name = "V271_DENIM_BREAKUP"
    noise.inputs["Scale"].default_value = 92.0
    noise.inputs["Detail"].default_value = 2.0
    bump = nodes.get("V271_DENIM_BUMP") or nodes.new("ShaderNodeBump")
    bump.name = "V271_DENIM_BUMP"
    bump.inputs["Strength"].default_value = 0.07
    bump.inputs["Distance"].default_value = 0.00018
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def make_mesh(name, verts, faces, collection, material):
    mesh = bpy.data.meshes.new(name + "_MESH")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    mesh.materials.append(material)
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    solid = obj.modifiers.new(name + "_THICKNESS", "SOLIDIFY")
    solid.thickness = 0.0042
    solid.offset = 0.0
    bevel = obj.modifiers.new(name + "_EDGE_SOFTEN", "BEVEL")
    bevel.width = 0.0020
    bevel.segments = 3
    sub = obj.modifiers.new(name + "_SUBDIV", "SUBSURF")
    sub.levels = 1
    sub.render_levels = 2
    armature = obj.modifiers.new(name + "_RIG", "ARMATURE")
    armature.object = bpy.data.objects[RIG]
    armature.use_deform_preserve_volume = True
    return obj


def torso_shell(collection, material):
    # z, half width, depth, center-y, front opening half-width.
    rings = [
        (0.900, 0.224, 0.137, 0.012, 0.060),
        (0.980, 0.226, 0.140, 0.012, 0.058),
        (1.080, 0.232, 0.143, 0.014, 0.057),
        (1.180, 0.242, 0.146, 0.016, 0.058),
        (1.280, 0.254, 0.149, 0.018, 0.062),
        (1.365, 0.263, 0.146, 0.020, 0.070),
        (1.430, 0.252, 0.136, 0.021, 0.082),
        (1.468, 0.205, 0.122, 0.020, 0.090),
    ]
    across = 31
    verts = []
    for z, rx, ry, cy, gap in rings:
        delta = math.asin(min(0.95, gap / rx))
        start = -math.pi / 2 + delta
        end = 3 * math.pi / 2 - delta
        for i in range(across):
            a = start + (end - start) * i / (across - 1)
            # Slightly flatten the front panels while retaining a shaped back.
            y = cy + ry * math.sin(a)
            if math.sin(a) < -0.75:
                y = max(y, cy - ry * 0.94)
            verts.append((rx * math.cos(a), y, z))
    faces = []
    for row in range(len(rings) - 1):
        for i in range(across - 1):
            a = row * across + i
            faces.append((a, a + 1, a + across + 1, a + across))
    obj = make_mesh("V271_JACKET_TORSO", verts, faces, collection, material)
    groups = [
        obj.vertex_groups.new(name="DEF-spine.002"),
        obj.vertex_groups.new(name="DEF-spine.003"),
        obj.vertex_groups.new(name="DEF-spine.004"),
        obj.vertex_groups.new(name="DEF-spine.005"),
    ]
    for row, (z, *_rest) in enumerate(rings):
        t = (z - rings[0][0]) / (rings[-1][0] - rings[0][0])
        pos = t * (len(groups) - 1)
        low = min(len(groups) - 1, int(pos))
        high = min(len(groups) - 1, low + 1)
        blend = pos - low
        indices = list(range(row * across, (row + 1) * across))
        groups[low].add(indices, 1.0 - blend, "REPLACE")
        if high != low:
            groups[high].add(indices, blend, "ADD")
    return obj


def sleeve(side, collection, material):
    sign = 1.0 if side == "L" else -1.0
    centers = [
        Vector((0.232 * sign, 0.012, 1.405)),
        Vector((0.258 * sign, 0.024, 1.345)),
        Vector((0.292 * sign, 0.031, 1.275)),
        Vector((0.326 * sign, 0.016, 1.145)),
        Vector((0.365 * sign, -0.002, 1.005)),
    ]
    radii = [(0.074, 0.069), (0.078, 0.072), (0.073, 0.067), (0.061, 0.058), (0.050, 0.048)]
    seg = 20
    verts = []
    for index, (center, radius) in enumerate(zip(centers, radii)):
        if index == 0:
            tangent = (centers[1] - centers[0]).normalized()
        elif index == len(centers) - 1:
            tangent = (centers[-1] - centers[-2]).normalized()
        else:
            tangent = (centers[index + 1] - centers[index - 1]).normalized()
        basis_a = tangent.cross(Vector((0, 1, 0)))
        if basis_a.length < 0.1:
            basis_a = tangent.cross(Vector((0, 0, 1)))
        basis_a.normalize()
        basis_b = tangent.cross(basis_a).normalized()
        for i in range(seg):
            angle = 2 * math.pi * i / seg
            co = center + basis_a * (math.cos(angle) * radius[0]) + basis_b * (math.sin(angle) * radius[1])
            verts.append(tuple(co))
    faces = []
    for row in range(len(centers) - 1):
        for i in range(seg):
            j = (i + 1) % seg
            faces.append((row * seg + i, row * seg + j, (row + 1) * seg + j, (row + 1) * seg + i))
    obj = make_mesh(f"V271_JACKET_SLEEVE_{side}", verts, faces, collection, material)
    upper_a = obj.vertex_groups.new(name=f"DEF-upper_arm.{side}")
    upper_b = obj.vertex_groups.new(name=f"DEF-upper_arm.{side}.001")
    fore_a = obj.vertex_groups.new(name=f"DEF-forearm.{side}")
    fore_b = obj.vertex_groups.new(name=f"DEF-forearm.{side}.001")
    weights = [(upper_a, 1.0), (upper_a, 0.55, upper_b, 0.45), (upper_b, 0.45, fore_a, 0.55), (fore_a, 0.55, fore_b, 0.45), (fore_b, 1.0)]
    for row, assignment in enumerate(weights):
        indices = list(range(row * seg, (row + 1) * seg))
        if len(assignment) == 2:
            assignment[0].add(indices, assignment[1], "REPLACE")
        else:
            assignment[0].add(indices, assignment[1], "REPLACE")
            assignment[2].add(indices, assignment[3], "ADD")
    return obj


def collar_band(collection, material):
    # Open collar base following the upper torso ellipse.
    verts, faces = [], []
    seg = 28
    for z, rx, ry in ((1.455, 0.205, 0.125), (1.505, 0.190, 0.116)):
        delta = math.asin(0.055 / rx)
        start, end = -math.pi / 2 + delta, 3 * math.pi / 2 - delta
        for i in range(seg):
            a = start + (end - start) * i / (seg - 1)
            verts.append((rx * math.cos(a), 0.020 + ry * math.sin(a), z))
    for i in range(seg - 1):
        faces.append((i, i + 1, seg + i + 1, seg + i))
    obj = make_mesh("V271_JACKET_COLLAR_BASE", verts, faces, collection, material)
    group = obj.vertex_groups.new(name="DEF-spine.005")
    group.add(list(range(len(verts))), 1.0, "REPLACE")
    return obj


def shoulder_cap(side, collection, material):
    sign = 1.0 if side == "L" else -1.0
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, location=(0.225 * sign, 0.018, 1.405))
    obj = bpy.context.object
    obj.name = f"V271_JACKET_SHOULDER_CAP_{side}"
    for old_collection in tuple(obj.users_collection):
        old_collection.objects.unlink(obj)
    collection.objects.link(obj)
    obj.scale = (0.092, 0.112, 0.090)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    shoulder = obj.vertex_groups.new(name=f"DEF-shoulder.{side}")
    upper = obj.vertex_groups.new(name=f"DEF-upper_arm.{side}")
    indices = [vertex.index for vertex in obj.data.vertices]
    shoulder.add(indices, 0.45, "REPLACE")
    upper.add(indices, 0.55, "ADD")
    armature = obj.modifiers.new(obj.name + "_RIG", "ARMATURE")
    armature.object = bpy.data.objects[RIG]
    armature.use_deform_preserve_volume = True
    return obj


def main():
    if Path(bpy.data.filepath).resolve() != SOURCE.resolve():
        raise RuntimeError(f"Open V270 first: {SOURCE}")
    STAGE.mkdir(parents=True, exist_ok=True)
    RENDERS.mkdir(parents=True, exist_ok=True)
    AUDIT.mkdir(parents=True, exist_ok=True)
    hidden = []
    prefixes = ("V262_", "V263_", "V266_", "V267_")
    for obj in bpy.context.scene.objects:
        if obj.name.startswith(prefixes):
            obj.hide_render = True
            obj.hide_viewport = True
            hidden.append(obj.name)
    collection = bpy.data.collections.get("V271_EXPLICIT_JACKET") or bpy.data.collections.new("V271_EXPLICIT_JACKET")
    if collection.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(collection)
    mat = jacket_material()
    pieces = [torso_shell(collection, mat), sleeve("L", collection, mat), sleeve("R", collection, mat)]

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.look = "AgX - Medium High Contrast"
    cam = bpy.data.objects["CAM_V211_FRONT"]
    rig = bpy.data.objects[RIG]
    hand = bpy.data.objects["V250_FRETTING_HAND_RIG"]
    old_rig, old_hand = rig.data.pose_position, hand.data.pose_position
    guitar = [obj for obj in scene.objects if obj.name.startswith("V206_")]
    guitar_state = {obj.name: (obj.hide_render, obj.hide_viewport) for obj in guitar}
    rig.data.pose_position = "REST"
    hand.data.pose_position = "REST"
    for obj in guitar:
        obj.hide_render = True
        obj.hide_viewport = True
    bpy.context.view_layer.update()
    views = {
        "neutral_front": (Vector((0, -3.65, 1.08)), Vector((0, 0, 1.08)), 72, (900, 1100)),
        "neutral_three_quarter": (Vector((-2.45, -2.70, 1.12)), Vector((0, 0, 1.10)), 76, (900, 1100)),
        "neutral_profile": (Vector((-3.20, 0.0, 1.10)), Vector((0, 0, 1.10)), 78, (900, 1100)),
        "upper_front": (Vector((0, -2.10, 1.28)), Vector((0, 0, 1.27)), 82, (1000, 1000)),
        "upper_rear": (Vector((0, 2.20, 1.28)), Vector((0, 0, 1.27)), 82, (1000, 1000)),
    }
    renders = {}
    for label, (location, target, lens, resolution) in views.items():
        cam.location = location
        cam.data.lens = lens
        point_at(cam, target)
        scene.camera = cam
        scene.render.resolution_x, scene.render.resolution_y = resolution
        scene.render.resolution_percentage = 100
        path = RENDERS / f"v271_{label}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        renders[label] = {"path": str(path.relative_to(ROOT)), "sha256": sha(path)}
    rig.data.pose_position, hand.data.pose_position = old_rig, old_hand
    for obj in guitar:
        obj.hide_render, obj.hide_viewport = guitar_state[obj.name]
    bpy.context.view_layer.update()
    record = {
        "schema": "v271-explicit-jacket-topology-v1",
        "status": "BUILT_VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)},
        "hidden_failed_branch": hidden,
        "pieces": [{"name": obj.name, "vertices": len(obj.data.vertices), "polygons": len(obj.data.polygons)} for obj in pieces],
        "renders": renders,
        "output": {"path": str(OUTPUT.relative_to(ROOT))},
    }
    scene["V271_STATUS"] = "EXPLICIT_JACKET_TOPOLOGY_VISUAL_REVIEW_REQUIRED"
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record["output"]["sha256"] = sha(OUTPUT)
    (AUDIT / "v271_explicit_jacket.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V271_EXPLICIT_JACKET_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
