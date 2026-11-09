"""Build the first reference-directed groom and skin pass on V216."""

from pathlib import Path
import math
import random

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
STAGE = ROOT / "production_v217_groom_skin"
OUTPUT = STAGE / "Character_An_groom_skin_v217.blend"
RENDER_DIR = STAGE / "renders"
STAGE.mkdir(parents=True, exist_ok=True)
RENDER_DIR.mkdir(parents=True, exist_ok=True)
random.seed(217031)


def material(name, color, roughness=0.45):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


def curve_object(name, bevel, mat):
    data = bpy.data.curves.new(name + "_DATA", "CURVE")
    data.dimensions = "3D"
    data.resolution_u = 1
    data.bevel_depth = bevel
    data.bevel_resolution = 2
    data.resolution_u = 1
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    data.materials.append(mat)
    return obj


def add_poly(curve, points, radius_start=1.0, radius_end=0.25):
    spline = curve.data.splines.new("POLY")
    spline.points.add(len(points) - 1)
    count = max(1, len(points) - 1)
    for index, point in enumerate(points):
        spline.points[index].co = (*point, 1.0)
        spline.points[index].radius = radius_start + (radius_end - radius_start) * index / count


for obj in list(bpy.data.objects):
    if obj.name.startswith("V217_"):
        bpy.data.objects.remove(obj, do_unlink=True)

head = bpy.data.objects["V216_REFERENCE_FITTED_HEAD"]
skin = head.data.materials[0]
skin.name = "V217_SKIN"
skin.use_nodes = True
nodes = skin.node_tree.nodes
links = skin.node_tree.links
bsdf = nodes.get("Principled BSDF")
bsdf.inputs["Base Color"].default_value = (0.235, 0.068, 0.025, 1.0)
bsdf.inputs["Roughness"].default_value = 0.52
if "Specular IOR Level" in bsdf.inputs:
    bsdf.inputs["Specular IOR Level"].default_value = 0.16
if "Subsurface Weight" in bsdf.inputs:
    bsdf.inputs["Subsurface Weight"].default_value = 0.075
if "Coat Weight" in bsdf.inputs:
    bsdf.inputs["Coat Weight"].default_value = 0.0
noise = nodes.get("V217_SKIN_MICRO") or nodes.new("ShaderNodeTexNoise")
noise.name = "V217_SKIN_MICRO"
noise.inputs["Scale"].default_value = 165.0
noise.inputs["Detail"].default_value = 3.0
noise.inputs["Roughness"].default_value = 0.68
bump = nodes.get("V217_SKIN_BUMP") or nodes.new("ShaderNodeBump")
bump.name = "V217_SKIN_BUMP"
bump.inputs["Strength"].default_value = 0.12
bump.inputs["Distance"].default_value = 0.0012
links.new(noise.outputs["Fac"], bump.inputs["Height"])
links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])

hair_mat = material("V217_HAIR", (0.012, 0.0060, 0.0030, 1.0), 0.58)
brow_mat = material("V217_BROW", (0.008, 0.004, 0.0025, 1.0), 0.58)
beard_mat = material("V217_BEARD", (0.012, 0.006, 0.0035, 1.0), 0.7)

# Dense short helical fibers form tight curls without a cap-like substrate.
hair = curve_object("V217_TIGHT_CURL_GROOM", 0.00092, hair_mat)
center = Vector((0.001, 0.010, 1.704))
rx, ry, rz = 0.128, 0.122, 0.112
for _ in range(2650):
    phi = random.uniform(0.0, math.tau)
    theta = math.acos(random.uniform(math.cos(1.22), 1.0))
    direction = Vector((math.sin(theta) * math.cos(phi), math.sin(theta) * math.sin(phi), math.cos(theta)))
    anchor = center + Vector((rx * direction.x, ry * direction.y, rz * direction.z))
    # Reference hairline: higher at temples, slightly lower at the front center.
    if anchor.y < -0.07:
        hairline = 1.704 + 0.018 * min(1.0, abs(anchor.x) / rx)
        if anchor.z < hairline:
            continue
    normal = Vector((direction.x / rx, direction.y / ry, direction.z / rz)).normalized()
    tangent = normal.cross(Vector((0.0, 0.0, 1.0)))
    if tangent.length < 0.1:
        tangent = Vector((1.0, 0.0, 0.0))
    tangent.normalize()
    bitangent = normal.cross(tangent).normalized()
    side_fade = max(0.58, min(1.0, (anchor.z - 1.660) / 0.095))
    length = random.uniform(0.018, 0.034) * side_fade
    radius = random.uniform(0.0030, 0.0052) * side_fade
    turns = random.uniform(1.15, 1.8)
    points = []
    for index in range(9):
        t = index / 8.0
        angle = turns * math.tau * t + random.uniform(-0.08, 0.08)
        point = anchor + normal * (length * t)
        point += (tangent * math.cos(angle) + bitangent * math.sin(angle)) * radius * math.sin(math.pi * t)
        points.append(point)
    add_poly(hair, points, 0.9, 0.18)

# Readable loop clusters carry the ringlet language visible in the reference.
clusters = curve_object("V217_CURL_CLUSTERS", 0.00105, hair_mat)
for _ in range(520):
    phi = random.uniform(0.0, math.tau)
    theta = math.acos(random.uniform(math.cos(1.12), 1.0))
    direction = Vector((math.sin(theta) * math.cos(phi), math.sin(theta) * math.sin(phi), math.cos(theta)))
    anchor = center + Vector((rx * direction.x, ry * direction.y, rz * direction.z))
    if anchor.y < -0.07 and anchor.z < 1.710 + 0.016 * min(1.0, abs(anchor.x) / rx):
        continue
    normal = Vector((direction.x / rx, direction.y / ry, direction.z / rz)).normalized()
    tangent = normal.cross(Vector((0.0, 0.0, 1.0)))
    if tangent.length < 0.1:
        tangent = Vector((1.0, 0.0, 0.0))
    tangent.normalize()
    bitangent = normal.cross(tangent).normalized()
    loop_radius = random.uniform(0.0038, 0.0060)
    loop_center = anchor + normal * random.uniform(0.014, 0.026)
    points = []
    for index in range(14):
        angle = math.tau * 1.15 * index / 13.0
        points.append(loop_center + tangent * math.cos(angle) * loop_radius + bitangent * math.sin(angle) * loop_radius + normal * (0.002 * math.sin(angle * 2.0)))
    add_poly(clusters, points, 0.95, 0.35)

# Brows use many tapered fibers following the heavy, nearly straight reference arches.
brows = curve_object("V217_BROWS", 0.00048, brow_mat)
for side in (-1.0, 1.0):
    brow_line = []
    for index in range(16):
        t = index / 15.0
        brow_line.append(Vector((
            side * (0.020 + 0.055 * t),
            -0.116 - 0.006 * math.sin(math.pi * t),
            1.704 + 0.006 * math.sin(math.pi * t),
        )))
    add_poly(brows, brow_line, 1.35, 0.55)
    for row in range(7):
        for index in range(18):
            t = index / 17.0
            x = side * (0.020 + 0.055 * t)
            z = 1.704 + 0.006 * math.sin(math.pi * t) - row * 0.00075
            y = -0.116 - 0.006 * math.sin(math.pi * t)
            start = Vector((x, y, z))
            direction = Vector((side * 0.003, -0.0012, 0.0015 + 0.001 * (0.5 - t)))
            add_poly(brows, [start, start + direction], 1.0, 0.12)

# Sample the fitted facial surface for short beard and moustache fibers.
beard = curve_object("V217_BEARD_STUBBLE", 0.00036, beard_mat)
matrix = head.matrix_world
normal_matrix = matrix.to_3x3()
selected = []
for vertex in head.data.vertices:
    point = matrix @ vertex.co
    jaw = 1.515 < point.z < 1.585 and point.y < -0.005 and abs(point.x) < 0.115
    cheek = 1.565 < point.z < 1.625 and point.y < -0.072 and 0.035 < abs(point.x) < 0.115
    moustache = 1.580 < point.z < 1.612 and point.y < -0.105 and abs(point.x) < 0.074
    lip_gap = 1.574 < point.z < 1.596 and point.y < -0.125 and abs(point.x) < 0.045
    if (jaw or cheek or moustache) and not lip_gap:
        selected.append(vertex)
random.shuffle(selected)
for vertex in selected[:2600]:
    point = matrix @ vertex.co
    normal = (normal_matrix @ vertex.normal).normalized()
    for _ in range(3):
        root_jitter = Vector((random.uniform(-0.0012, 0.0012), random.uniform(-0.0006, 0.0006), random.uniform(-0.0012, 0.0012)))
        length = random.uniform(0.0025, 0.0070)
        tip_jitter = Vector((random.uniform(-0.0010, 0.0010), random.uniform(-0.0006, 0.0006), random.uniform(-0.0010, 0.0010)))
        root = point + root_jitter
        add_poly(beard, [root, root + normal * length + tip_jitter], 0.82, 0.05)

for obj in (hair, clusters, brows, beard):
    obj.hide_render = False

scene = bpy.context.scene
scene["V217_STATUS"] = "REFERENCE_DIRECTED_GROOM_SKIN_CANDIDATE"
scene["V217_HAIR_SPLINES"] = len(hair.data.splines)
scene["V217_BEARD_SPLINES"] = len(beard.data.splines)
scene["V217_BROW_SPLINES"] = len(brows.data.splines)

camera = bpy.data.objects["V216_CAMERA"]
target = Vector((0.0, -0.015, 1.575))
views = {
    "front": Vector((0.0, -2.25, 1.62)),
    "left_three_quarter": Vector((-1.25, -1.75, 1.64)),
    "left_profile": Vector((-2.25, 0.0, 1.62)),
}
scene.render.resolution_x = 768
scene.render.resolution_y = 900
for name, location in views.items():
    camera.location = location
    camera.rotation_euler = (target - location).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = str(RENDER_DIR / f"v217_{name}.png")
    bpy.ops.render.render(write_still=True)

bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
print({
    "status": "ok",
    "output": str(OUTPUT),
    "hair_splines": len(hair.data.splines),
    "beard_splines": len(beard.data.splines),
    "brow_splines": len(brows.data.splines),
})
