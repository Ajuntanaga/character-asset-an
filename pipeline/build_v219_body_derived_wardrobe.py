"""Create continuous fitted wardrobe shells from the current evaluated body."""

from pathlib import Path
import math

import bmesh
import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
STAGE = ROOT / "production_v219_body_derived_wardrobe"
OUTPUT = STAGE / "Character_An_wardrobe_v219.blend"
RENDER_DIR = STAGE / "renders"
STAGE.mkdir(parents=True, exist_ok=True)
RENDER_DIR.mkdir(parents=True, exist_ok=True)

for obj in list(bpy.data.objects):
    if obj.name.startswith("V219_"):
        bpy.data.objects.remove(obj, do_unlink=True)

body = bpy.data.objects["V216_BODY_WITH_NECK_STUB"]
depsgraph = bpy.context.evaluated_depsgraph_get()
evaluated = body.evaluated_get(depsgraph)
base_mesh = bpy.data.meshes.new_from_object(evaluated, depsgraph=depsgraph)
base_matrix = body.matrix_world.copy()
for vertex in base_mesh.vertices:
    vertex.co = base_matrix @ vertex.co


def make_material(name, color, roughness, noise_scale=None, noise_strength=0.08):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = roughness
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.18
    if noise_scale:
        noise = nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = noise_scale
        noise.inputs["Detail"].default_value = 2.0
        bump = nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = noise_strength
        bump.inputs["Distance"].default_value = 0.001
        links.new(noise.outputs["Fac"], bump.inputs["Height"])
        links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


jacket_mat = make_material("V219_CHARCOAL_DENIM", (0.018, 0.022, 0.024, 1.0), 0.72, 210.0, 0.12)
trouser_mat = make_material("V219_BLACK_DENIM", (0.009, 0.010, 0.011, 1.0), 0.76, 190.0, 0.10)
shirt_mat = make_material("V219_DARK_FLORAL_SHIRT", (0.075, 0.045, 0.025, 1.0), 0.62, 7.0, 0.05)
leather_mat = make_material("V219_BROWN_BOOT_LEATHER", (0.12, 0.032, 0.010, 1.0), 0.34, 28.0, 0.10)
sole_mat = make_material("V219_BOOT_SOLE", (0.015, 0.010, 0.008, 1.0), 0.72, 55.0, 0.08)
metal_mat = make_material("V219_BRASS", (0.20, 0.095, 0.025, 1.0), 0.32)
metal_bsdf = metal_mat.node_tree.nodes.get("Principled BSDF")
metal_bsdf.inputs["Metallic"].default_value = 0.7

# Dark floral variation using object coordinates; the sparse ochre islands read
# as the small botanical print in the approved turnaround without relying on
# the old body's UV layout.
shirt_nodes = shirt_mat.node_tree.nodes
shirt_links = shirt_mat.node_tree.links
shirt_bsdf = shirt_nodes.get("Principled BSDF")
floral_noise = shirt_nodes.new("ShaderNodeTexNoise")
floral_noise.name = "V219_FLORAL_NOISE"
floral_noise.inputs["Scale"].default_value = 18.0
floral_noise.inputs["Detail"].default_value = 5.0
floral_noise.inputs["Roughness"].default_value = 0.72
floral_ramp = shirt_nodes.new("ShaderNodeValToRGB")
floral_ramp.name = "V219_FLORAL_RAMP"
floral_ramp.color_ramp.elements[0].position = 0.38
floral_ramp.color_ramp.elements[0].color = (0.006, 0.003, 0.002, 1.0)
floral_ramp.color_ramp.elements[1].position = 0.62
floral_ramp.color_ramp.elements[1].color = (0.19, 0.065, 0.012, 1.0)
shirt_links.new(floral_noise.outputs["Fac"], floral_ramp.inputs["Fac"])
shirt_links.new(floral_ramp.outputs["Color"], shirt_bsdf.inputs["Base Color"])


def shell(name, predicate, material, thickness=0.0035, outward=1.0):
    mesh = base_mesh.copy()
    bm = bmesh.new()
    bm.from_mesh(mesh)
    remove = [vert for vert in bm.verts if not predicate(vert.co)]
    bmesh.ops.delete(bm, geom=remove, context="VERTS")
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.clear()
    obj.data.materials.append(material)
    displace = obj.modifiers.new(name + "_RELAX", "DISPLACE")
    displace.strength = thickness * 1.6
    displace.mid_level = 0.0
    solid = obj.modifiers.new(name + "_SOLIDIFY", "SOLIDIFY")
    solid.thickness = thickness
    solid.offset = outward
    smooth = obj.modifiers.new(name + "_SMOOTH", "SMOOTH")
    smooth.factor = 0.18
    smooth.iterations = 2
    for polygon in mesh.polygons:
        polygon.use_smooth = True
        polygon.material_index = 0
    obj.hide_render = False
    return obj


shirt = shell(
    "V219_FITTED_SHIRT",
    lambda p: 0.82 < p.z < 1.49 and abs(p.x) < 0.245,
    shirt_mat,
    0.0030,
)
jacket = shell(
    "V219_OPEN_JACKET",
    lambda p: (
        0.84 < p.z < 1.49
        and not (p.y < -0.045 and abs(p.x) < 0.115)
        and not (abs(p.x) > 0.36 and p.z < 1.24)
    ),
    jacket_mat,
    0.0060,
)
trousers = shell(
    "V219_TAPERED_TROUSERS",
    lambda p: 0.13 < p.z < 1.035,
    trouser_mat,
    0.0045,
)
boots = shell(
    "V219_FITTED_BOOT_UPPERS",
    lambda p: p.z < 0.29,
    leather_mat,
    0.0060,
)
boot_soles = shell(
    "V219_FITTED_BOOT_SOLES",
    lambda p: p.z < 0.070,
    sole_mat,
    0.0070,
)


def add_beveled_cube(name, location, scale, material, bevel=0.012):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bevel_mod = obj.modifiers.new(name + "_BEVEL", "BEVEL")
    bevel_mod.width = bevel
    bevel_mod.segments = 3
    obj.data.materials.append(material)
    obj.hide_render = False
    return obj


# Shirt placket and seven brass buttons.
add_beveled_cube("V219_SHIRT_PLACKET", (0.0, -0.184, 1.185), (0.010, 0.004, 0.265), shirt_mat, 0.003)
for index in range(7):
    z = 1.425 - index * 0.078
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=0.007, location=(0.0, -0.192, z))
    button = bpy.context.object
    button.name = f"V219_SHIRT_BUTTON_{index + 1:02d}"
    button.scale.y = 0.35
    button.data.materials.append(metal_mat)

# Compact collar wedges cover the head/body seam and sit beneath the jacket.
for side in (-1.0, 1.0):
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=0.075, radius2=0.035, depth=0.09, location=(side * 0.055, -0.105, 1.445), rotation=(math.radians(78), 0.0, side * math.radians(22)))
    collar = bpy.context.object
    collar.name = "V219_SHIRT_COLLAR_L" if side > 0 else "V219_SHIRT_COLLAR_R"
    collar.data.materials.append(shirt_mat)
    collar.hide_render = False

    lapel = add_beveled_cube(
        "V219_JACKET_LAPEL_L" if side > 0 else "V219_JACKET_LAPEL_R",
        (side * 0.132, -0.146, 1.315),
        (0.038, 0.009, 0.165),
        jacket_mat,
        0.008,
    )
    lapel.rotation_euler.y = side * math.radians(11.0)
    pocket = add_beveled_cube(
        "V219_JACKET_POCKET_L" if side > 0 else "V219_JACKET_POCKET_R",
        (side * 0.190, -0.154, 1.225),
        (0.060, 0.008, 0.064),
        jacket_mat,
        0.006,
    )

# Hide naked torso/legs where the continuous shells cover them; hands/head remain visible.
body.hide_render = False

camera_data = bpy.data.cameras.new("V219_CAMERA_DATA")
camera_data.lens = 72.0
camera = bpy.data.objects.new("V219_CAMERA", camera_data)
bpy.context.scene.collection.objects.link(camera)


def point_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


target = Vector((0.0, 0.0, 0.93))
for name, location, energy, size in (
    ("KEY", (-2.8, -3.8, 3.8), 1000.0, 4.0),
    ("FILL", (2.8, -2.4, 2.2), 480.0, 3.5),
    ("RIM", (2.0, 2.8, 3.2), 720.0, 3.0),
):
    data = bpy.data.lights.new(f"V219_{name}_DATA", "AREA")
    data.energy = energy
    data.size = size
    light = bpy.data.objects.new(f"V219_{name}", data)
    bpy.context.scene.collection.objects.link(light)
    light.location = location
    point_at(light, target)

scene = bpy.context.scene
scene.camera = camera
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 720
scene.render.resolution_y = 960
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.world.color = (0.018, 0.018, 0.018)
views = {
    "front": Vector((0.0, -4.15, 1.0)),
    "left_three_quarter": Vector((-2.7, -3.15, 1.05)),
    "left_profile": Vector((-4.15, 0.0, 1.0)),
}
for name, location in views.items():
    camera.location = location
    point_at(camera, target)
    scene.render.filepath = str(RENDER_DIR / f"v219_{name}.png")
    bpy.ops.render.render(write_still=True)

scene["V219_STATUS"] = "BODY_DERIVED_WARDROBE_VISUAL_CANDIDATE"
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
print({"status": "ok", "output": str(OUTPUT), "garments": [shirt.name, jacket.name, trousers.name, boots.name]})
