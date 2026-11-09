"""Replace jagged legacy shells with clean rig-weighted reference wardrobe."""

from pathlib import Path
import hashlib
import json
import math

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v281_dynamic_oral_shader" / "Character_An_dynamic_oral_shader_v281.blend"
STAGE = ROOT / "production_v282_clean_wardrobe"
OUTPUT = STAGE / "Character_An_clean_wardrobe_v282.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"
BODY = "V211_BODY_NEUTRAL"
RIG = "V239_CLEAN_CHARACTER_RIG"


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            digest.update(block)
    return digest.hexdigest()


def point_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def principled_material(name, base, roughness, metallic=0.0, noise_scale=None, accent=None):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    shader.inputs["Base Color"].default_value = (*base, 1.0)
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Metallic"].default_value = metallic
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    if noise_scale:
        tex = nodes.new("ShaderNodeTexNoise")
        tex.inputs["Scale"].default_value = noise_scale
        tex.inputs["Detail"].default_value = 5.0
        tex.inputs["Roughness"].default_value = 0.72
        ramp = nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].color = (*base, 1.0)
        ramp.color_ramp.elements[1].color = (*(accent or tuple(min(1.0, c * 1.6) for c in base)), 1.0)
        bump = nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = 0.12
        bump.inputs["Distance"].default_value = 0.0012
        links.new(tex.outputs["Fac"], ramp.inputs["Fac"])
        links.new(ramp.outputs["Color"], shader.inputs["Base Color"])
        links.new(tex.outputs["Fac"], bump.inputs["Height"])
        links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    return mat


def floral_material():
    mat = principled_material("V282_FLORAL_SHIRT", (0.055, 0.035, 0.018), 0.62)
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    shader = next(node for node in nodes if node.type == "BSDF_PRINCIPLED")
    tex = nodes.new("ShaderNodeTexVoronoi")
    tex.distance = "EUCLIDEAN"
    tex.feature = "DISTANCE_TO_EDGE"
    tex.inputs["Scale"].default_value = 28.0
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 7.0
    noise.inputs["Detail"].default_value = 4.0
    mix = nodes.new("ShaderNodeMixRGB")
    mix.blend_type = "MULTIPLY"
    mix.inputs[1].default_value = (0.12, 0.075, 0.025, 1.0)
    mix.inputs[2].default_value = (0.82, 0.58, 0.24, 1.0)
    links.new(tex.outputs["Distance"], mix.inputs[0])
    links.new(mix.outputs[0], shader.inputs["Base Color"])
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.08
    bump.inputs["Distance"].default_value = 0.0008
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    return mat


def mesh_object(name, vertices, faces, material, smooth=True):
    mesh = bpy.data.meshes.new(name + "_MESH")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    mesh.materials.append(material)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    for polygon in mesh.polygons:
        polygon.use_smooth = smooth
    return obj


def elliptical_shell(name, rings, segments, material, gap=0.0):
    vertices, faces = [], []
    if gap:
        angles = [-math.pi / 2 + gap + (2 * math.pi - 2 * gap) * i / (segments - 1) for i in range(segments)]
        wrap = False
    else:
        angles = [2 * math.pi * i / segments for i in range(segments)]
        wrap = True
    for z, rx, ry, cy in rings:
        vertices.extend((rx * math.cos(angle), cy + ry * math.sin(angle), z) for angle in angles)
    for ring in range(len(rings) - 1):
        limit = segments if wrap else segments - 1
        for i in range(limit):
            j = (i + 1) % segments
            a, b = ring * segments + i, ring * segments + j
            c, d = (ring + 1) * segments + j, (ring + 1) * segments + i
            faces.append((a, b, c, d))
    obj = mesh_object(name, vertices, faces, material)
    solid = obj.modifiers.new("Garment thickness", "SOLIDIFY")
    solid.thickness = 0.0045
    solid.offset = 0.0
    bevel = obj.modifiers.new("Soft garment edges", "BEVEL")
    bevel.width = 0.0025
    bevel.segments = 2
    return obj


def tube_between(name, start, end, r0, r1, material, segments=24, rings=8):
    start, end = Vector(start), Vector(end)
    direction = (end - start).normalized()
    axis_u = Vector((0.0, 1.0, 0.0))
    if abs(direction.dot(axis_u)) > 0.9:
        axis_u = Vector((1.0, 0.0, 0.0))
    axis_v = direction.cross(axis_u).normalized()
    axis_u = axis_v.cross(direction).normalized()
    vertices, faces = [], []
    for ring in range(rings):
        t = ring / (rings - 1)
        center = start.lerp(end, t)
        radius = r0 * (1.0 - t) + r1 * t
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            vertices.append(center + axis_u * (math.cos(angle) * radius * 0.92) + axis_v * (math.sin(angle) * radius))
    for ring in range(rings - 1):
        for i in range(segments):
            j = (i + 1) % segments
            faces.append((ring * segments + i, ring * segments + j, (ring + 1) * segments + j, (ring + 1) * segments + i))
    obj = mesh_object(name, vertices, faces, material)
    solid = obj.modifiers.new("Sleeve thickness", "SOLIDIFY")
    solid.thickness = 0.004
    solid.offset = 0.0
    return obj


def add_beveled_cube(name, location, scale, material, bevel=0.02):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.view_layer.objects.active
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    mod = obj.modifiers.new("Rounded tailoring", "BEVEL")
    mod.width = bevel
    mod.segments = 3
    return obj


def bind_to_body(obj, body, rig):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    transfer = obj.modifiers.new("V282_BODY_WEIGHT_TRANSFER", "DATA_TRANSFER")
    transfer.object = body
    transfer.use_vert_data = True
    transfer.data_types_verts = {"VGROUP_WEIGHTS"}
    transfer.vert_mapping = "POLYINTERP_NEAREST"
    try:
        bpy.ops.object.modifier_apply(modifier=transfer.name)
    except RuntimeError:
        obj.modifiers.remove(transfer)
    armature = obj.modifiers.new("V282_RIG", "ARMATURE")
    armature.object = rig
    obj.select_set(False)


def parent_bone(obj, rig, bone):
    world = obj.matrix_world.copy()
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = bone
    obj.matrix_world = world


def render(scene, camera, path):
    scene.camera = camera
    scene.render.resolution_x = 768
    scene.render.resolution_y = 1024
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(path)}


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    for folder in (STAGE, RENDERS, AUDIT):
        folder.mkdir(parents=True, exist_ok=True)
    body, rig = bpy.data.objects[BODY], bpy.data.objects[RIG]
    denim = principled_material("V282_CHARCOAL_DENIM", (0.018, 0.022, 0.026), 0.66, noise_scale=115.0, accent=(0.035, 0.045, 0.055))
    shirt_mat = floral_material()
    trouser_mat = principled_material("V282_DARK_TROUSERS", (0.012, 0.015, 0.018), 0.70, noise_scale=90.0, accent=(0.028, 0.032, 0.038))
    leather = principled_material("V282_BROWN_LEATHER", (0.15, 0.055, 0.018), 0.43, noise_scale=14.0, accent=(0.30, 0.12, 0.035))
    metal = principled_material("V282_BRASS", (0.30, 0.18, 0.055), 0.30, metallic=0.65)

    garments = []
    shirt = elliptical_shell("V282_FLORAL_SHIRT_BODY", [(0.96, .185, .115, .005), (1.10, .205, .128, .004), (1.27, .215, .138, .002), (1.43, .225, .142, .004), (1.52, .185, .118, .000)], 64, shirt_mat)
    garments.append(shirt)
    jacket = elliptical_shell("V282_DENIM_JACKET_BODY", [(0.98, .202, .128, .006), (1.12, .224, .143, .005), (1.30, .238, .153, .004), (1.47, .245, .156, .007), (1.54, .205, .132, .004)], 64, denim, gap=0.38)
    garments.append(jacket)
    arm_specs = {
        "L": ((.175, .008, 1.46), (.350, -.002, 1.065)),
        "R": ((-.175, .008, 1.46), (-.350, -.002, 1.065)),
    }
    for side, (start, end) in arm_specs.items():
        garments.append(tube_between(f"V282_JACKET_SLEEVE_{side}", start, end, .091, .062, denim))
    # Tailored trouser tubes plus a joined waist shell.
    waist = elliptical_shell("V282_TROUSER_WAIST", [(0.78, .175, .125, .012), (0.99, .190, .132, .010)], 64, trouser_mat)
    garments.append(waist)
    for side, x in (("L", .092), ("R", -.092)):
        garments.append(tube_between(f"V282_TROUSER_LEG_{side}", (x, .005, .90), (x, .010, .14), .105, .068, trouser_mat, rings=12))

    # Clean lapels, collar, pockets, seams, and buttons establish the jacket read.
    details = []
    details.append(add_beveled_cube("V282_LAPEL_L", (.075, -.157, 1.40), (.055, .008, .150), denim, .006))
    details.append(add_beveled_cube("V282_LAPEL_R", (-.075, -.157, 1.40), (.055, .008, .150), denim, .006))
    details[-2].rotation_euler.y = -0.22
    details[-1].rotation_euler.y = 0.22
    for side, x in (("L", .125), ("R", -.125)):
        details.append(add_beveled_cube(f"V282_CHEST_POCKET_{side}", (x, -.158, 1.30), (.055, .010, .050), denim, .005))
    for z in (1.08, 1.17, 1.26, 1.35, 1.44):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=10, location=(0.0, -.166, z), scale=(.010, .006, .010))
        button = bpy.context.view_layer.objects.active
        button.name = f"V282_JACKET_BUTTON_{z:.2f}"
        button.data.materials.append(metal)
        details.append(button)

    for garment in garments + details:
        bind_to_body(garment, body, rig)

    # Reference Chelsea boots, kept rigid to the feet.
    boot_objects = []
    for side, x, bone in (("L", .093, "foot_fk.L"), ("R", -.093, "foot_fk.R")):
        shaft = add_beveled_cube(f"V282_BOOT_SHAFT_{side}", (x, .015, .155), (.078, .095, .120), leather, .025)
        toe = add_beveled_cube(f"V282_BOOT_TOE_{side}", (x, -.115, .075), (.082, .155, .060), leather, .035)
        sole = add_beveled_cube(f"V282_BOOT_SOLE_{side}", (x, -.085, .024), (.088, .170, .018), principled_material("V282_BOOT_SOLE", (.012, .009, .006), .78), .012)
        heel = add_beveled_cube(f"V282_BOOT_HEEL_{side}", (x, .055, .050), (.070, .070, .040), bpy.data.materials["V282_BOOT_SOLE"], .010)
        for obj in (shaft, toe, sole, heel):
            parent_bone(obj, rig, bone)
            boot_objects.append(obj)

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    camera_data = bpy.data.cameras.new("V282_FULL_CAMERA_DATA")
    camera = bpy.data.objects.new("V282_FULL_CAMERA", camera_data)
    scene.collection.objects.link(camera)
    camera.location = Vector((0.0, -5.25, 1.00))
    camera.data.lens = 72.0
    point_at(camera, Vector((0.0, 0.0, .93)))
    renders = {"front": render(scene, camera, RENDERS / "v282_wardrobe_front.png")}
    camera.location = Vector((-3.2, -4.15, 1.15))
    point_at(camera, Vector((0.0, 0.0, .98)))
    renders["three_quarter"] = render(scene, camera, RENDERS / "v282_wardrobe_three_quarter.png")
    scene["V282_STATUS"] = "CLEAN_WARDROBE_VISUAL_REVIEW_REQUIRED"
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v282-clean-wardrobe-v1",
        "status": "BUILT_VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)},
        "garments": [obj.name for obj in garments],
        "details": [obj.name for obj in details],
        "boots": [obj.name for obj in boot_objects],
        "renders": renders,
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha(OUTPUT)},
    }
    (AUDIT / "v282_clean_wardrobe.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V282_CLEAN_WARDROBE_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
