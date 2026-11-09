from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.common import sha256, write_json


STAGE = ROOT / "production_v205_wardrobe"
SOURCE = ROOT / "production_v204_groom" / "ant_groomed_character_v204.blend"
OUTPUT = STAGE / "ant_wardrobe_boots_v205.blend"
EXPECTED_SOURCE_SHA256 = "a89599481394c5802fcc9214ec153b1645a3410128bbd6e1cba50aabeaed60d1"
EXPECTED_V200_SHA256 = "42612cfbd1cbeed03c0db1eb085ea10f1ca73fe3697404ad563d1cb15599c6d1"
EXPECTED_V192_SHA256 = "443321b43df4ada529113854f935b393e2e523fbbd36beb08c53fb0d08048148"

REFERENCE_LOCK = "open charcoal work jacket; dark floral button shirt; deep-black tapered rolled-cuff trousers; brown Chelsea boots; left-chest pen"

RENDER_VIEWS = {
    "front": ("V205_CAM_FRONT", (560, 720)),
    "three_quarter": ("V205_CAM_THREE_QUARTER", (560, 720)),
    "profile": ("V205_CAM_PROFILE", (560, 720)),
    "rear": ("V205_CAM_REAR", (560, 720)),
    "torso_detail": ("V205_CAM_TORSO", (640, 640)),
    "boots_detail": ("V205_CAM_BOOTS", (640, 480)),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def set_input(node: bpy.types.Node, name: str, value: object) -> None:
    socket = node.inputs.get(name)
    if socket is not None:
        socket.default_value = value


def tag(obj: bpy.types.Object, role: str) -> bpy.types.Object:
    obj["v205_procedural_final"] = True
    obj["wardrobe_role"] = role
    obj["reference_authority"] = "supplied character sheets"
    return obj


def relink(obj: bpy.types.Object, collection: bpy.types.Collection) -> None:
    for owner in list(obj.users_collection):
        owner.objects.unlink(obj)
    collection.objects.link(obj)


def assign(obj: bpy.types.Object, material: bpy.types.Material) -> None:
    obj.data.materials.clear()
    obj.data.materials.append(material)


def smooth(obj: bpy.types.Object) -> None:
    if obj.type == "MESH":
        for polygon in obj.data.polygons:
            polygon.use_smooth = True


def fabric_material(
    name: str,
    physical_class: str,
    dark: tuple[float, float, float, float],
    light: tuple[float, float, float, float],
    roughness: float,
    weave_scale: float,
) -> bpy.types.Material:
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    principled = nodes.new("ShaderNodeBsdfPrincipled")
    principled.name = "Principled BSDF"
    set_input(principled, "Roughness", roughness)
    set_input(principled, "IOR", 1.46)
    set_input(principled, "Specular IOR Level", 0.22)
    set_input(principled, "Sheen Weight", 0.10)
    texcoord = nodes.new("ShaderNodeTexCoord")
    noise = nodes.new("ShaderNodeTexNoise")
    set_input(noise, "Scale", weave_scale)
    set_input(noise, "Detail", 3.0)
    set_input(noise, "Roughness", 0.66)
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.22
    ramp.color_ramp.elements[0].color = dark
    ramp.color_ramp.elements[1].position = 0.78
    ramp.color_ramp.elements[1].color = light
    bump = nodes.new("ShaderNodeBump")
    set_input(bump, "Strength", 0.16)
    set_input(bump, "Distance", 0.00018)
    links.new(texcoord.outputs["Generated"], noise.inputs["Vector"])
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], principled.inputs["Base Color"])
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], principled.inputs["Normal"])
    links.new(principled.outputs["BSDF"], output.inputs["Surface"])
    material.diffuse_color = dark
    material["physical_class"] = physical_class
    material["weave_scale"] = weave_scale
    return material


def floral_material() -> bpy.types.Material:
    material = bpy.data.materials.get("MAT_V205_DARK_FLORAL_SHIRT") or bpy.data.materials.new("MAT_V205_DARK_FLORAL_SHIRT")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    principled = nodes.new("ShaderNodeBsdfPrincipled")
    principled.name = "Principled BSDF"
    set_input(principled, "Roughness", 0.56)
    set_input(principled, "IOR", 1.45)
    set_input(principled, "Specular IOR Level", 0.24)
    set_input(principled, "Sheen Weight", 0.08)
    texcoord = nodes.new("ShaderNodeTexCoord")
    voronoi = nodes.new("ShaderNodeTexVoronoi")
    set_input(voronoi, "Scale", 22.0)
    set_input(voronoi, "Randomness", 0.78)
    ramp = nodes.new("ShaderNodeValToRGB")
    colors = ramp.color_ramp
    colors.elements.remove(colors.elements[1])
    palette = [
        (0.18, (0.005, 0.009, 0.014, 1.0)),
        (0.38, (0.065, 0.018, 0.011, 1.0)),
        (0.56, (0.24, 0.075, 0.018, 1.0)),
        (0.72, (0.12, 0.16, 0.055, 1.0)),
        (0.86, (0.42, 0.30, 0.10, 1.0)),
    ]
    colors.elements[0].position, colors.elements[0].color = palette[0]
    for position, color in palette[1:]:
        element = colors.elements.new(position)
        element.color = color
    noise = nodes.new("ShaderNodeTexNoise")
    set_input(noise, "Scale", 170.0)
    set_input(noise, "Detail", 2.0)
    bump = nodes.new("ShaderNodeBump")
    set_input(bump, "Strength", 0.11)
    set_input(bump, "Distance", 0.00012)
    links.new(texcoord.outputs["Generated"], voronoi.inputs["Vector"])
    links.new(texcoord.outputs["Generated"], noise.inputs["Vector"])
    links.new(voronoi.outputs["Distance"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], principled.inputs["Base Color"])
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], principled.inputs["Normal"])
    links.new(principled.outputs["BSDF"], output.inputs["Surface"])
    material.diffuse_color = (0.012, 0.016, 0.020, 1.0)
    material["physical_class"] = "printed_dark_flower_weave"
    material["pattern"] = "small low-contrast ochre rust olive floral on near-black ground"
    return material


def leather_material() -> bpy.types.Material:
    material = bpy.data.materials.get("MAT_V205_BROWN_BOOT_LEATHER") or bpy.data.materials.new("MAT_V205_BROWN_BOOT_LEATHER")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    principled = nodes.new("ShaderNodeBsdfPrincipled")
    principled.name = "Principled BSDF"
    set_input(principled, "Base Color", (0.115, 0.035, 0.014, 1.0))
    set_input(principled, "Roughness", 0.39)
    set_input(principled, "IOR", 1.50)
    set_input(principled, "Specular IOR Level", 0.34)
    set_input(principled, "Coat Weight", 0.11)
    set_input(principled, "Coat Roughness", 0.28)
    texcoord = nodes.new("ShaderNodeTexCoord")
    noise = nodes.new("ShaderNodeTexNoise")
    set_input(noise, "Scale", 82.0)
    set_input(noise, "Detail", 7.0)
    set_input(noise, "Roughness", 0.72)
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.025, 0.006, 0.003, 1.0)
    ramp.color_ramp.elements[1].color = (0.19, 0.055, 0.018, 1.0)
    bump = nodes.new("ShaderNodeBump")
    set_input(bump, "Strength", 0.22)
    set_input(bump, "Distance", 0.00028)
    links.new(texcoord.outputs["Generated"], noise.inputs["Vector"])
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], principled.inputs["Base Color"])
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], principled.inputs["Normal"])
    links.new(principled.outputs["BSDF"], output.inputs["Surface"])
    material.diffuse_color = (0.115, 0.035, 0.014, 1.0)
    material["physical_class"] = "full_grain_brown_leather"
    return material


def simple_material(name: str, physical_class: str, color: tuple[float, float, float, float], roughness: float, metallic: float = 0.0) -> bpy.types.Material:
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.use_nodes = True
    principled = material.node_tree.nodes.get("Principled BSDF")
    require(principled is not None, f"Missing Principled shader: {name}")
    set_input(principled, "Base Color", color)
    set_input(principled, "Roughness", roughness)
    set_input(principled, "Metallic", metallic)
    material.diffuse_color = color
    material["physical_class"] = physical_class
    return material


def make_mesh(name: str, vertices: list[tuple[float, float, float]], faces: list[tuple[int, ...]], collection: bpy.types.Collection, material: bpy.types.Material, role: str) -> bpy.types.Object:
    mesh = bpy.data.meshes.new(name + "_MESH")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    assign(obj, material)
    smooth(obj)
    tag(obj, role)
    return obj


def add_solidify_subdivision(obj: bpy.types.Object, thickness: float, levels: int = 2) -> None:
    solidify = obj.modifiers.new("V205_CLOTH_THICKNESS", "SOLIDIFY")
    solidify.thickness = thickness
    solidify.offset = 0.0
    solidify.use_rim = True
    subdivision = obj.modifiers.new("V205_TAILORING_SUBDIVISION", "SUBSURF")
    subdivision.subdivision_type = "CATMULL_CLARK"
    subdivision.levels = levels
    subdivision.render_levels = levels


def loft_ellipse(
    name: str,
    rings: list[tuple[float, float, float]],
    collection: bpy.types.Collection,
    material: bpy.types.Material,
    role: str,
    segments: int = 48,
    open_front_half_angle: float | None = None,
) -> bpy.types.Object:
    if open_front_half_angle is None:
        angles = [math.tau * index / segments for index in range(segments)]
        cyclic = True
    else:
        angles = [(-math.pi + open_front_half_angle) + (2.0 * (math.pi - open_front_half_angle)) * index / (segments - 1) for index in range(segments)]
        cyclic = False
    vertices: list[tuple[float, float, float]] = []
    for z, radius_x, radius_y in rings:
        for angle in angles:
            vertices.append((radius_x * math.sin(angle), radius_y * math.cos(angle), z))
    faces: list[tuple[int, ...]] = []
    ring_count = len(rings)
    edge_count = segments if cyclic else segments - 1
    for ring in range(ring_count - 1):
        for index in range(edge_count):
            nxt = (index + 1) % segments
            a = ring * segments + index
            b = ring * segments + nxt
            c = (ring + 1) * segments + nxt
            d = (ring + 1) * segments + index
            faces.append((a, b, c, d))
    obj = make_mesh(name, vertices, faces, collection, material, role)
    add_solidify_subdivision(obj, 0.0022 if "JACKET" in name else 0.0012)
    return obj


def tube_along_path(
    name: str,
    centers: list[tuple[float, float, float]],
    radii: list[tuple[float, float]],
    collection: bpy.types.Collection,
    material: bpy.types.Material,
    role: str,
    segments: int = 24,
) -> bpy.types.Object:
    require(len(centers) == len(radii), f"Tube path/radius mismatch: {name}")
    points = [Vector(point) for point in centers]
    vertices: list[tuple[float, float, float]] = []
    for index, (center, (radius_depth, radius_vertical)) in enumerate(zip(points, radii)):
        if index == 0:
            direction = (points[1] - center).normalized()
        elif index == len(points) - 1:
            direction = (center - points[index - 1]).normalized()
        else:
            direction = (points[index + 1] - points[index - 1]).normalized()
        depth_axis = Vector((0.0, 1.0, 0.0))
        if abs(direction.dot(depth_axis)) > 0.92:
            depth_axis = Vector((0.0, 0.0, 1.0))
        vertical_axis = direction.cross(depth_axis).normalized()
        depth_axis = vertical_axis.cross(direction).normalized()
        for segment in range(segments):
            angle = math.tau * segment / segments
            point = center + depth_axis * math.cos(angle) * radius_depth + vertical_axis * math.sin(angle) * radius_vertical
            vertices.append(tuple(point))
    faces: list[tuple[int, ...]] = []
    for ring in range(len(points) - 1):
        for segment in range(segments):
            nxt = (segment + 1) % segments
            faces.append((ring * segments + segment, ring * segments + nxt, (ring + 1) * segments + nxt, (ring + 1) * segments + segment))
    obj = make_mesh(name, vertices, faces, collection, material, role)
    add_solidify_subdivision(obj, 0.0020, 1)
    return obj


def panel(name: str, points: list[tuple[float, float, float]], collection: bpy.types.Collection, material: bpy.types.Material, role: str, thickness: float = 0.0020) -> bpy.types.Object:
    obj = make_mesh(name, points, [tuple(range(len(points)))], collection, material, role)
    add_solidify_subdivision(obj, thickness, 1)
    return obj


def rounded_box(
    name: str,
    location: tuple[float, float, float],
    dimensions: tuple[float, float, float],
    collection: bpy.types.Collection,
    material: bpy.types.Material,
    role: str,
    bevel: float,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    relink(obj, collection)
    assign(obj, material)
    edge = obj.modifiers.new("V205_EDGE_RADIUS", "BEVEL")
    edge.width = bevel
    edge.segments = 4
    tag(obj, role)
    return obj


def curve_detail(name: str, points: list[tuple[float, float, float]], bevel: float, collection: bpy.types.Collection, material: bpy.types.Material, role: str, cyclic: bool = False) -> bpy.types.Object:
    curve = bpy.data.curves.new(name + "_CURVE", "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 2
    curve.bevel_depth = bevel
    curve.bevel_resolution = 2
    spline = curve.splines.new("NURBS" if len(points) > 2 else "POLY")
    spline.points.add(len(points) - 1)
    for point, coordinate in zip(spline.points, points):
        point.co = (*coordinate, 1.0)
    if spline.type == "NURBS":
        spline.order_u = min(3, len(points))
        spline.use_endpoint_u = not cyclic
        spline.use_cyclic_u = cyclic
    curve.materials.append(material)
    obj = bpy.data.objects.new(name, curve)
    collection.objects.link(obj)
    tag(obj, role)
    return obj


def build_shirt(collection: bpy.types.Collection, floral: bpy.types.Material, button: bpy.types.Material) -> list[bpy.types.Object]:
    created: list[bpy.types.Object] = []
    shirt = loft_ellipse(
        "V205_SHIRT_BODY",
        [(1.035, 0.174, 0.118), (1.18, 0.177, 0.126), (1.34, 0.187, 0.134), (1.47, 0.174, 0.118), (1.515, 0.105, 0.088)],
        collection,
        floral,
        "fully buttoned dark floral shirt shell",
    )
    shirt["fit_clearance_m"] = 0.006
    created.append(shirt)
    created.append(rounded_box("V205_SHIRT_PLACKET", (0.0, -0.1375, 1.275), (0.017, 0.004, 0.405), collection, floral, "shirt button placket", 0.0012))
    for index, z in enumerate((1.115, 1.175, 1.235, 1.295, 1.355, 1.415, 1.468), 1):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=0.0052, location=(0.0, -0.143, z))
        obj = bpy.context.object
        obj.name = f"V205_SHIRT_BUTTON_{index:02d}"
        obj.scale = (1.0, 0.45, 1.0)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        relink(obj, collection)
        assign(obj, button)
        tag(obj, "seven-button shirt closure")
        created.append(obj)
    created.extend(
        [
            panel("V205_SHIRT_COLLAR_L", [(0.008, -0.137, 1.487), (0.090, -0.108, 1.503), (0.055, -0.142, 1.425), (0.010, -0.146, 1.451)], collection, floral, "shirt collar left"),
            panel("V205_SHIRT_COLLAR_R", [(-0.008, -0.137, 1.487), (-0.090, -0.108, 1.503), (-0.055, -0.142, 1.425), (-0.010, -0.146, 1.451)], collection, floral, "shirt collar right"),
        ]
    )
    return created


def build_jacket(collection: bpy.types.Collection, jacket_mat: bpy.types.Material, thread_mat: bpy.types.Material, pen_mat: bpy.types.Material) -> list[bpy.types.Object]:
    created: list[bpy.types.Object] = []
    body = loft_ellipse(
        "V205_JACKET_BODY",
        [(1.020, 0.204, 0.137), (1.19, 0.205, 0.146), (1.36, 0.218, 0.153), (1.47, 0.236, 0.148)],
        collection,
        jacket_mat,
        "open charcoal work jacket body",
        open_front_half_angle=0.36,
    )
    body["opening_width_m"] = 0.145
    body["fit_clearance_m"] = 0.010
    created.append(body)
    sleeve_paths = {
        "L": [(0.190, 0.000, 1.425), (0.255, -0.002, 1.355), (0.315, -0.008, 1.245), (0.375, -0.013, 1.125), (0.425, -0.018, 1.025)],
        "R": [(-0.190, 0.000, 1.425), (-0.255, -0.002, 1.355), (-0.315, -0.008, 1.245), (-0.375, -0.013, 1.125), (-0.425, -0.018, 1.025)],
    }
    for side, centers in sleeve_paths.items():
        sleeve = tube_along_path(
            f"V205_JACKET_SLEEVE_{side}",
            centers,
            [(0.082, 0.092), (0.076, 0.083), (0.068, 0.073), (0.058, 0.062), (0.052, 0.055)],
            collection,
            jacket_mat,
            f"neutral A-pose jacket sleeve {side}",
        )
        sleeve["neutral_a_pose_axis"] = centers
        created.append(sleeve)
        sign = 1.0 if side == "L" else -1.0
        created.append(
            tube_along_path(
                f"V205_JACKET_CUFF_{side}",
                [(sign * 0.402, -0.016, 1.073), (sign * 0.438, -0.019, 1.000)],
                [(0.055, 0.059), (0.052, 0.055)],
                collection,
                jacket_mat,
                f"jacket cuff {side}",
                24,
            )
        )
    created.extend(
        [
            panel("V205_JACKET_LAPEL_L", [(0.073, -0.146, 1.468), (0.154, -0.130, 1.420), (0.100, -0.160, 1.235), (0.061, -0.162, 1.335)], collection, jacket_mat, "open jacket lapel left", 0.0027),
            panel("V205_JACKET_LAPEL_R", [(-0.073, -0.146, 1.468), (-0.154, -0.130, 1.420), (-0.100, -0.160, 1.235), (-0.061, -0.162, 1.335)], collection, jacket_mat, "open jacket lapel right", 0.0027),
        ]
    )
    for side, x in (("L", 0.137), ("R", -0.137)):
        pocket = rounded_box(f"V205_JACKET_POCKET_{side}", (x, -0.158, 1.295), (0.069, 0.008, 0.094), collection, jacket_mat, f"work jacket chest pocket {side}", 0.003)
        flap = rounded_box(f"V205_JACKET_POCKET_FLAP_{side}", (x, -0.164, 1.347), (0.075, 0.006, 0.020), collection, jacket_mat, f"work jacket pocket flap {side}", 0.002)
        seam = curve_detail(f"V205_JACKET_POCKET_SEAM_{side}", [(x - 0.032, -0.164, 1.337), (x - 0.032, -0.164, 1.252), (x + 0.032, -0.164, 1.252), (x + 0.032, -0.164, 1.337)], 0.00055, collection, thread_mat, "tailoring stitch")
        created.extend([pocket, flap, seam])
    created.extend(
        [
            curve_detail("V205_JACKET_HEM_STITCH", [(-0.190, -0.128, 1.030), (0.0, 0.139, 1.018), (0.190, -0.128, 1.030)], 0.00055, collection, thread_mat, "jacket hem stitch"),
            curve_detail("V205_JACKET_FRONT_STITCH_L", [(0.071, -0.161, 1.045), (0.071, -0.164, 1.260), (0.073, -0.149, 1.462)], 0.00055, collection, thread_mat, "jacket front topstitch"),
            curve_detail("V205_JACKET_FRONT_STITCH_R", [(-0.071, -0.161, 1.045), (-0.071, -0.164, 1.260), (-0.073, -0.149, 1.462)], 0.00055, collection, thread_mat, "jacket front topstitch"),
        ]
    )
    pen = rounded_box("V205_PEN", (0.137, -0.171, 1.372), (0.008, 0.008, 0.105), collection, pen_mat, "pen in anatomical-left chest pocket", 0.002)
    pen.rotation_euler.y = math.radians(-4.0)
    created.append(pen)
    return created


def build_trousers(collection: bpy.types.Collection, trouser_mat: bpy.types.Material, thread_mat: bpy.types.Material) -> list[bpy.types.Object]:
    created: list[bpy.types.Object] = []
    hip = loft_ellipse(
        "V205_TROUSERS_HIP",
        [(0.84, 0.176, 0.120), (0.95, 0.185, 0.132), (1.045, 0.181, 0.130)],
        collection,
        trouser_mat,
        "deep-black trouser waist and seat",
        48,
    )
    created.append(hip)
    for side, sign in (("L", 1.0), ("R", -1.0)):
        centers = [(sign * 0.095, 0.0, 0.910), (sign * 0.112, 0.0, 0.755), (sign * 0.150, -0.002, 0.575), (sign * 0.192, -0.005, 0.395), (sign * 0.221, -0.008, 0.285)]
        leg = tube_along_path(
            f"V205_TROUSER_LEG_{side}",
            centers,
            [(0.099, 0.104), (0.090, 0.094), (0.080, 0.083), (0.069, 0.073), (0.061, 0.064)],
            collection,
            trouser_mat,
            f"tapered trouser leg {side}",
            28,
        )
        leg["taper_ratio"] = 0.616
        cuff = tube_along_path(
            f"V205_TROUSER_CUFF_{side}",
            [(sign * 0.211, -0.007, 0.330), (sign * 0.226, -0.009, 0.274)],
            [(0.067, 0.071), (0.064, 0.067)],
            collection,
            trouser_mat,
            f"rolled trouser cuff {side}",
            28,
        )
        cuff["rolled_cuff_height_m"] = 0.056
        crease = curve_detail(f"V205_TROUSER_CREASE_{side}", [(sign * 0.100, -0.106, 0.86), (sign * 0.145, -0.086, 0.58), (sign * 0.213, -0.073, 0.32)], 0.00045, collection, thread_mat, "pressed trouser crease")
        created.extend([leg, cuff, crease])
    waistband = rounded_box("V205_TROUSER_WAISTBAND", (0.0, 0.0, 1.025), (0.365, 0.259, 0.036), collection, trouser_mat, "trouser waistband", 0.008)
    created.append(waistband)
    return created


def build_boots(
    collection: bpy.types.Collection,
    leather: bpy.types.Material,
    elastic: bpy.types.Material,
    sole_mat: bpy.types.Material,
    thread_mat: bpy.types.Material,
) -> list[bpy.types.Object]:
    created: list[bpy.types.Object] = []
    for side, sign in (("L", 1.0), ("R", -1.0)):
        x = sign * 0.240
        foot = rounded_box(f"V205_BOOT_{side}", (x, -0.055, 0.095), (0.160, 0.365, 0.145), collection, leather, f"brown leather Chelsea boot {side}", 0.042)
        foot["construction"] = "Chelsea ankle boot with elastic gore and pull tab"
        shaft = rounded_box(f"V205_BOOT_SHAFT_{side}", (x, 0.022, 0.205), (0.150, 0.235, 0.290), collection, leather, f"Chelsea ankle shaft {side}", 0.032)
        sole = rounded_box(f"V205_BOOT_SOLE_{side}", (x, -0.060, 0.026), (0.168, 0.378, 0.032), collection, sole_mat, f"boot outsole {side}", 0.012)
        heel = rounded_box(f"V205_BOOT_HEEL_{side}", (x, 0.060, 0.030), (0.137, 0.102, 0.050), collection, sole_mat, f"stacked boot heel {side}", 0.010)
        gore = rounded_box(f"V205_BOOT_ELASTIC_{side}", (x + sign * 0.064, 0.013, 0.192), (0.006, 0.082, 0.092), collection, elastic, f"Chelsea elastic gore {side}", 0.003)
        welt = curve_detail(f"V205_BOOT_WELT_{side}", [(x - 0.066, -0.226, 0.050), (x - 0.071, -0.060, 0.047), (x - 0.062, 0.090, 0.050), (x + 0.062, 0.090, 0.050), (x + 0.071, -0.060, 0.047), (x + 0.066, -0.226, 0.050)], 0.0011, collection, thread_mat, f"boot welt stitch {side}")
        tab = curve_detail(f"V205_BOOT_PULL_TAB_{side}", [(x, 0.087, 0.260), (x, 0.090, 0.315), (x, 0.075, 0.276)], 0.0042, collection, leather, f"Chelsea pull tab {side}")
        created.extend([foot, shaft, sole, heel, gore, welt, tab])
    return created


def add_camera(name: str, location: tuple[float, float, float], target: tuple[float, float, float], focal_length: float, collection: bpy.types.Collection) -> bpy.types.Object:
    data = bpy.data.cameras.new(name + "_DATA")
    data.lens = focal_length
    data.sensor_width = 36.0
    obj = bpy.data.objects.new(name, data)
    collection.objects.link(obj)
    obj.location = location
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    obj["v205_acceptance_camera"] = True
    return obj


def add_area(name: str, location: tuple[float, float, float], energy: float, size: float, color: tuple[float, float, float], target: tuple[float, float, float], collection: bpy.types.Collection) -> bpy.types.Object:
    data = bpy.data.lights.new(name + "_DATA", "AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size
    data.color = color
    obj = bpy.data.objects.new(name, data)
    collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()
    return obj


def setup_cameras_lights(collection: bpy.types.Collection) -> dict[str, bpy.types.Object]:
    cameras = {
        "V205_CAM_FRONT": add_camera("V205_CAM_FRONT", (0.0, -4.55, 0.94), (0.0, 0.0, 0.92), 74.0, collection),
        "V205_CAM_THREE_QUARTER": add_camera("V205_CAM_THREE_QUARTER", (2.90, -3.55, 1.02), (0.0, 0.0, 0.93), 76.0, collection),
        "V205_CAM_PROFILE": add_camera("V205_CAM_PROFILE", (4.55, 0.0, 0.98), (0.0, 0.0, 0.92), 76.0, collection),
        "V205_CAM_REAR": add_camera("V205_CAM_REAR", (0.0, 4.55, 0.98), (0.0, 0.0, 0.92), 74.0, collection),
        "V205_CAM_TORSO": add_camera("V205_CAM_TORSO", (0.0, -2.30, 1.28), (0.0, -0.02, 1.27), 86.0, collection),
        "V205_CAM_BOOTS": add_camera("V205_CAM_BOOTS", (1.18, -2.05, 0.28), (0.0, -0.03, 0.18), 82.0, collection),
    }
    add_area("V205_KEY", (-2.0, -2.6, 3.0), 950.0, 2.2, (1.0, 0.86, 0.72), (0.0, 0.0, 1.0), collection)
    add_area("V205_FILL", (2.4, -1.0, 2.0), 600.0, 2.7, (0.70, 0.82, 1.0), (0.0, 0.0, 1.0), collection)
    add_area("V205_RIM", (0.0, 2.6, 2.7), 850.0, 1.8, (0.90, 0.95, 1.0), (0.0, 0.0, 1.15), collection)
    return cameras


def render_suite(cameras: dict[str, bpy.types.Object]) -> dict[str, dict[str, object]]:
    render_dir = STAGE / "renders" / "wardrobe"
    render_dir.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 32
    scene.cycles.use_denoising = True
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = 0.035
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = False
    scene.render.resolution_percentage = 100
    scene.render.image_settings.color_depth = "8"
    scene.view_settings.look = "AgX - Medium High Contrast"
    if scene.world is None:
        scene.world = bpy.data.worlds.new("V205_WORLD")
    scene.world.use_nodes = True
    background = scene.world.node_tree.nodes.get("Background")
    if background:
        background.inputs["Color"].default_value = (0.015, 0.020, 0.026, 1.0)
        background.inputs["Strength"].default_value = 0.22

    results: dict[str, dict[str, object]] = {}
    for label, (camera_name, resolution) in RENDER_VIEWS.items():
        scene.camera = cameras[camera_name]
        scene.render.resolution_x, scene.render.resolution_y = resolution
        output = render_dir / f"{label}.png"
        scene.render.filepath = str(output)
        bpy.ops.render.render(write_still=True)
        results[label] = {
            "camera": camera_name,
            "path": str(output.relative_to(ROOT)),
            "sha256": sha256(output),
            "renderer": "Cycles CPU",
            "samples": 32,
            "resolution": list(resolution),
        }
    return results


def main() -> None:
    require(Path(bpy.data.filepath).resolve() == SOURCE.resolve(), f"Open accepted V204 before building V205: {bpy.data.filepath}")
    require(sha256(SOURCE) == EXPECTED_SOURCE_SHA256, "Accepted V204 source hash changed")
    require(bpy.context.scene.get("checkpoint") == "V204_GROOM", "V205 must build directly on V204_GROOM")
    require(sha256(ROOT / "production_v200_final" / "ant_character_asset_final_v200.blend") == EXPECTED_V200_SHA256, "Protected V200 changed")
    require(sha256(ROOT / "ant_compact_pick_pinch_v192.blend") == EXPECTED_V192_SHA256, "Protected V192 changed")

    old = bpy.data.collections.get("V205_WARDROBE")
    if old is not None:
        for obj in list(old.all_objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(old)
    collection = bpy.data.collections.new("V205_WARDROBE")
    bpy.context.scene.collection.children.link(collection)

    jacket = fabric_material("MAT_V205_CHARCOAL_JACKET", "woven_charcoal_workwear", (0.010, 0.013, 0.016, 1.0), (0.045, 0.052, 0.058, 1.0), 0.72, 135.0)
    floral = floral_material()
    trousers = fabric_material("MAT_V205_TRUE_BLACK_TROUSERS", "deep_black_twill", (0.0015, 0.0018, 0.0022, 1.0), (0.012, 0.014, 0.017, 1.0), 0.78, 165.0)
    leather = leather_material()
    elastic = fabric_material("MAT_V205_BOOT_ELASTIC", "ribbed_black_elastic", (0.003, 0.004, 0.005, 1.0), (0.020, 0.023, 0.025, 1.0), 0.84, 210.0)
    sole = simple_material("MAT_V205_BOOT_SOLE", "matte_boot_rubber", (0.006, 0.006, 0.005, 1.0), 0.88)
    thread = simple_material("MAT_V205_TAILORING_THREAD", "polyester_tailoring_thread", (0.020, 0.023, 0.026, 1.0), 0.62)
    button = simple_material("MAT_V205_SHIRT_BUTTON", "dark_horn_button", (0.025, 0.018, 0.012, 1.0), 0.34)
    pen_mat = simple_material("MAT_V205_PEN", "black_lacquer_pen", (0.010, 0.012, 0.016, 1.0), 0.24, 0.15)

    created = []
    created.extend(build_shirt(collection, floral, button))
    created.extend(build_jacket(collection, jacket, thread, pen_mat))
    created.extend(build_trousers(collection, trousers, thread))
    created.extend(build_boots(collection, leather, elastic, sole, thread))
    cameras = setup_cameras_lights(collection)

    scene = bpy.context.scene
    scene["checkpoint"] = "V205_WARDROBE_BOOTS"
    scene["checkpoint_intent"] = "photoreal-oriented fitted wardrobe and Chelsea boots on the accepted neutral A-pose"
    scene["source_v204_sha256"] = EXPECTED_SOURCE_SHA256
    scene["reference_authority"] = "supplied sheets > analytic M3 > generated guidance"
    scene["v205_reference_lock"] = REFERENCE_LOCK
    scene["v205_jacket_opening_width_m"] = 0.145
    scene["v205_trouser_thigh_width_m"] = 0.198
    scene["v205_trouser_hem_width_m"] = 0.122
    scene["v205_rolled_cuff_height_m"] = 0.056
    scene["v205_neutral_a_pose_compatible"] = True
    scene["v205_legacy_geometry_policy"] = "V195 read-only visual reference; zero V195 geometry reused"

    supplied_turnaround = ROOT / "references" / "turnaround" / "character_turnaround_v2_face_refined.png"
    supplied_design = ROOT / "references" / "source" / "approved_character_design_lock.png"
    audit = {
        "schema": "v205-wardrobe-audit-v1",
        "checkpoint": "V205_WARDROBE_BOOTS",
        "authority": "supplied",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha256(SOURCE)},
        "reference_lock": REFERENCE_LOCK,
        "neutral_a_pose_compatible": True,
        "legacy_v195_reused": False,
        "construction": "procedural lofted cloth shells, A-pose sleeve tubes, separate tailoring details, rounded Chelsea components",
        "materials": {
            value.name: {"physical_class": value.get("physical_class"), "node_count": len(value.node_tree.nodes)}
            for value in (jacket, floral, trousers, leather, elastic, sole)
        },
        "created_objects": sorted(obj.name for obj in created),
        "fit_contract": {
            "jacket_opening_width_m": 0.145,
            "shirt_body_clearance_m": 0.006,
            "jacket_body_clearance_m": 0.010,
            "trouser_taper_ratio": 0.616,
            "rolled_cuff_height_m": 0.056,
            "sleeves_follow_neutral_a_pose": True,
        },
        "references": [
            {"path": str(supplied_turnaround.relative_to(ROOT)), "sha256": sha256(supplied_turnaround), "authority": "supplied"},
            {"path": str(supplied_design.relative_to(ROOT)), "sha256": sha256(supplied_design), "authority": "supplied"},
        ],
    }
    write_json(STAGE / "audit" / "v205_wardrobe_audit.json", audit)

    render_results = render_suite(cameras)
    write_json(
        STAGE / "audit" / "v205_render_manifest.json",
        {
            "schema": "v205-render-manifest-v1",
            "checkpoint": "V205_WARDROBE_BOOTS",
            "renderer": "Cycles CPU",
            "renders": render_results,
        },
    )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), compress=True)
    require(OUTPUT.is_file(), "V205 checkpoint was not saved")
    output_hash = sha256(OUTPUT)
    receipt = {
        "status": "PASS",
        "checkpoint": "V205_WARDROBE_BOOTS",
        "blender_version": bpy.app.version_string,
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha256(SOURCE)},
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": output_hash, "bytes": OUTPUT.stat().st_size},
        "wardrobe_audit": {"path": str((STAGE / "audit" / "v205_wardrobe_audit.json").relative_to(ROOT)), "sha256": sha256(STAGE / "audit" / "v205_wardrobe_audit.json")},
        "render_manifest": {"path": str((STAGE / "audit" / "v205_render_manifest.json").relative_to(ROOT)), "sha256": sha256(STAGE / "audit" / "v205_render_manifest.json")},
        "garment_objects": len(created),
        "renders": len(render_results),
        "protected_hashes": {"V200": EXPECTED_V200_SHA256, "V192": EXPECTED_V192_SHA256},
    }
    write_json(STAGE / "audit" / "v205_build_receipt.json", receipt)
    print(f"V205_BUILD_OK output={OUTPUT.relative_to(ROOT)} sha256={output_hash} garments={len(created)} renders={len(render_results)}")


if __name__ == "__main__":
    main()
