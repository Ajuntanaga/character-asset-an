from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.common import sha256, write_json
from pipeline.guitar_geometry import GuitarGeometry, load_authoritative_mapping


STAGE = ROOT / "production_v206_guitar"
SOURCE = ROOT / "production_v205_wardrobe" / "ant_wardrobe_boots_v205.blend"
OUTPUT = STAGE / "ant_headless_guitar_v206.blend"
# Lead replaces this token after V205 is accepted. Keeping one conspicuous token
# prevents an unverified upstream file from silently becoming canonical.
EXPECTED_SOURCE_SHA256 = "c97bdaed781fa1114b19e397a1ea7287ffb714b36b2e71f7492615fb66958713"
EXPECTED_V200_SHA256 = "42612cfbd1cbeed03c0db1eb085ea10f1ca73fe3697404ad563d1cb15599c6d1"
EXPECTED_V192_SHA256 = "443321b43df4ada529113854f935b393e2e523fbbd36beb08c53fb0d08048148"

STRING_GAUGES_IN = (0.074, 0.064, 0.054, 0.042, 0.032, 0.024, 0.016, 0.010)
NEUTRAL_FRET_X = 0.260
BODY_OUTLINE = (
    (0.472, 0.047), (0.438, 0.098), (0.398, 0.190), (0.500, 0.174),
    (0.680, 0.222), (0.875, 0.180), (0.960, 0.083), (0.922, 0.014),
    (0.968, -0.116), (0.868, -0.204), (0.675, -0.220), (0.503, -0.151),
    (0.418, -0.181), (0.456, -0.082), (0.472, -0.047),
)
RENDER_VIEWS = {
    "front": ("V206_CAM_FRONT", (900, 640), "catalog"),
    "back": ("V206_CAM_BACK", (900, 640), "catalog"),
    "beauty": ("V206_CAM_BEAUTY", (900, 640), "grazing"),
    "bridge_macro": ("V206_CAM_BRIDGE", (768, 640), "macro"),
    "controls_macro": ("V206_CAM_CONTROLS", (768, 640), "macro"),
    "fretboard_macro": ("V206_CAM_FRETBOARD", (900, 640), "macro"),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def collection(name: str) -> bpy.types.Collection:
    value = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if value.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(value)
    return value


def link_object(name: str, data, target: bpy.types.Collection) -> bpy.types.Object:
    obj = bpy.data.objects.new(name, data)
    target.objects.link(obj)
    return obj


def principled_material(
    name: str,
    base_color: tuple[float, float, float, float],
    roughness: float,
    metallic: float = 0.0,
    anisotropic: float = 0.0,
) -> bpy.types.Material:
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    surface = nodes.new("ShaderNodeBsdfPrincipled")
    surface.inputs["Base Color"].default_value = base_color
    surface.inputs["Roughness"].default_value = roughness
    surface.inputs["Metallic"].default_value = metallic
    surface.inputs["IOR"].default_value = 1.48 if metallic == 0.0 else 1.50
    if "Anisotropic" in surface.inputs:
        surface.inputs["Anisotropic"].default_value = anisotropic
    links.new(surface.outputs["BSDF"], output.inputs["Surface"])
    material.diffuse_color = base_color
    material["v206_pbr"] = True
    material["roughness"] = roughness
    material["metallic"] = metallic
    return material


def figured_top_material() -> bpy.types.Material:
    material = bpy.data.materials.get("MAT_V206_FIGURED_CHARCOAL") or bpy.data.materials.new("MAT_V206_FIGURED_CHARCOAL")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    surface = nodes.new("ShaderNodeBsdfPrincipled")
    texcoord = nodes.new("ShaderNodeTexCoord")
    mapping = nodes.new("ShaderNodeMapping")
    noise = nodes.new("ShaderNodeTexNoise")
    ramp = nodes.new("ShaderNodeValToRGB")
    bump = nodes.new("ShaderNodeBump")
    mapping.inputs["Scale"].default_value = (2.5, 34.0, 4.0)
    noise.inputs["Scale"].default_value = 4.2
    noise.inputs["Detail"].default_value = 7.0
    noise.inputs["Roughness"].default_value = 0.68
    noise.inputs["Distortion"].default_value = 1.25
    ramp.color_ramp.elements[0].position = 0.25
    ramp.color_ramp.elements[0].color = (0.0015, 0.0020, 0.0025, 1.0)
    ramp.color_ramp.elements[1].position = 0.78
    ramp.color_ramp.elements[1].color = (0.028, 0.034, 0.038, 1.0)
    surface.inputs["Roughness"].default_value = 0.25
    surface.inputs["Coat Weight"].default_value = 0.20
    surface.inputs["Coat Roughness"].default_value = 0.18
    bump.inputs["Strength"].default_value = 0.13
    bump.inputs["Distance"].default_value = 0.00035
    links.new(texcoord.outputs["Generated"], mapping.inputs["Vector"])
    links.new(mapping.outputs["Vector"], noise.inputs["Vector"])
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], surface.inputs["Base Color"])
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], surface.inputs["Normal"])
    links.new(surface.outputs["BSDF"], output.inputs["Surface"])
    material.diffuse_color = (0.055, 0.065, 0.066, 1.0)
    material["v206_pbr"] = True
    material["finish"] = "smoky_charcoal_figured_wood_satin"
    return material


def maple_material() -> bpy.types.Material:
    material = bpy.data.materials.get("MAT_V206_MAPLE") or bpy.data.materials.new("MAT_V206_MAPLE")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    surface = nodes.new("ShaderNodeBsdfPrincipled")
    texcoord = nodes.new("ShaderNodeTexCoord")
    mapping = nodes.new("ShaderNodeMapping")
    noise = nodes.new("ShaderNodeTexNoise")
    ramp = nodes.new("ShaderNodeValToRGB")
    mapping.inputs["Scale"].default_value = (1.2, 48.0, 5.0)
    noise.inputs["Scale"].default_value = 3.0
    noise.inputs["Detail"].default_value = 5.0
    noise.inputs["Roughness"].default_value = 0.45
    ramp.color_ramp.elements[0].color = (0.30, 0.135, 0.045, 1.0)
    ramp.color_ramp.elements[1].color = (0.88, 0.57, 0.25, 1.0)
    surface.inputs["Roughness"].default_value = 0.34
    surface.inputs["Coat Weight"].default_value = 0.08
    links.new(texcoord.outputs["Generated"], mapping.inputs["Vector"])
    links.new(mapping.outputs["Vector"], noise.inputs["Vector"])
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], surface.inputs["Base Color"])
    links.new(surface.outputs["BSDF"], output.inputs["Surface"])
    material.diffuse_color = (0.58, 0.31, 0.105, 1.0)
    material["v206_pbr"] = True
    material["species_look"] = "roasted_maple"
    return material


def extruded_polygon(
    name: str,
    points: tuple[tuple[float, float], ...],
    z_bottom: float,
    z_top: float,
    material: bpy.types.Material,
    target: bpy.types.Collection,
    bevel: float = 0.0,
) -> bpy.types.Object:
    count = len(points)
    vertices = [(x, y, z_bottom) for x, y in points] + [(x, y, z_top) for x, y in points]
    faces: list[tuple[int, ...]] = [tuple(reversed(range(count))), tuple(range(count, count * 2))]
    for index in range(count):
        nxt = (index + 1) % count
        faces.append((index, nxt, count + nxt, count + index))
    mesh = bpy.data.meshes.new(f"{name}_MESH")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = link_object(name, mesh, target)
    obj.data.materials.append(material)
    if bevel:
        modifier = obj.modifiers.new("Physical edge roll", "BEVEL")
        modifier.width = bevel
        modifier.segments = 4
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    return obj


def tapered_prism(
    name: str,
    x0: float,
    x1: float,
    half_y0: float,
    half_y1: float,
    z0: float,
    z1: float,
    material: bpy.types.Material,
    target: bpy.types.Collection,
    bevel: float = 0.0,
) -> bpy.types.Object:
    points = ((x0, -half_y0), (x1, -half_y1), (x1, half_y1), (x0, half_y0))
    return extruded_polygon(name, points, z0, z1, material, target, bevel)


def curve_segments(
    name: str,
    segments: list[list[tuple[float, float, float]]],
    bevel_depth: float,
    material: bpy.types.Material,
    target: bpy.types.Collection,
) -> bpy.types.Object:
    data = bpy.data.curves.new(f"{name}_CURVE", "CURVE")
    data.dimensions = "3D"
    data.resolution_u = 2
    data.bevel_resolution = 3
    data.bevel_depth = bevel_depth
    data.materials.append(material)
    for segment in segments:
        spline = data.splines.new("POLY")
        spline.points.add(len(segment) - 1)
        for point, co in zip(spline.points, segment):
            point.co = (*co, 1.0)
    return link_object(name, data, target)


def cube(
    name: str,
    location: tuple[float, float, float],
    scale: tuple[float, float, float],
    material: bpy.types.Material,
    target: bpy.types.Collection,
    bevel: float = 0.0,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    for owner in tuple(obj.users_collection):
        owner.objects.unlink(obj)
    target.objects.link(obj)
    obj.data.materials.append(material)
    if bevel:
        modifier = obj.modifiers.new("Machined edge", "BEVEL")
        modifier.width = bevel
        modifier.segments = 3
    return obj


def cylinder(
    name: str,
    location: tuple[float, float, float],
    radius: float,
    depth: float,
    material: bpy.types.Material,
    target: bpy.types.Collection,
    vertices: int = 32,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    for owner in tuple(obj.users_collection):
        owner.objects.unlink(obj)
    target.objects.link(obj)
    obj.data.materials.append(material)
    bevel = obj.modifiers.new("Machined edge", "BEVEL")
    bevel.width = min(radius * 0.10, depth * 0.10)
    bevel.segments = 3
    return obj


def remove_legacy_guitar() -> list[str]:
    legacy = set()
    old_collection = bpy.data.collections.get("ANT_STRANDBERG_BLOCKOUT")
    if old_collection:
        legacy.update(old_collection.all_objects)
    for obj in bpy.data.objects:
        if obj.name.startswith(("V178_", "V186_")) or obj.name == "V166_PICK":
            legacy.add(obj)
    removed = sorted(obj.name for obj in legacy)
    for obj in legacy:
        bpy.data.objects.remove(obj, do_unlink=True)
    if old_collection:
        bpy.data.collections.remove(old_collection)
    return removed


def parent_to_root(objects: list[bpy.types.Object], root: bpy.types.Object) -> None:
    for obj in objects:
        if obj != root and obj.type not in {"CAMERA", "LIGHT"}:
            obj.parent = root


def physical_point(geometry: GuitarGeometry, string_id: str, fret: int) -> Vector:
    """Map per-string nut distances into one physical fan with F7 straight."""
    point = geometry.string_fret_wire_point(string_id, fret)
    neutral = geometry.string_fret_wire_point(string_id, geometry.neutral_fret)
    return Vector((NEUTRAL_FRET_X + point[0] - neutral[0], point[1], point[2]))


def physical_nut_bridge(geometry: GuitarGeometry, string_id: str) -> tuple[Vector, Vector]:
    spec = geometry.strings[string_id]
    nut = physical_point(geometry, string_id, 0)
    return nut, Vector((nut.x + spec.scale_m, spec.bridge_y_m, 0.0))


def add_hardware(
    target: bpy.types.Collection,
    geometry: GuitarGeometry,
    materials: dict[str, bpy.types.Material],
) -> list[bpy.types.Object]:
    objects: list[bpy.types.Object] = []
    black, steel = materials["black"], materials["steel"]

    for pickup_name, x in (("NECK", 0.590), ("BRIDGE", 0.660)):
        pickup = cube(f"V206_PICKUP_{pickup_name}", (x, 0.0, 0.015), (0.026, 0.047, 0.007), black, target, 0.003)
        pickup["type"] = "eight_string_soapbar"
        objects.append(pickup)
        for index, string_id in enumerate(geometry.string_ids_low_to_high):
            spec = geometry.strings[string_id]
            nut, _bridge = physical_nut_bridge(geometry, string_id)
            progress = (x - nut.x) / spec.scale_m
            y = spec.nut_y_m + (spec.bridge_y_m - spec.nut_y_m) * progress
            pole = cylinder(f"V206_{pickup_name}_POLE_{string_id}", (x, y, 0.0225), 0.0023, 0.0010, steel, target, 20)
            pole["string_id"] = string_id
            objects.append(pole)
        for screw_index, y in enumerate((-0.041, 0.041), 1):
            screw = cylinder(
                f"V206_{pickup_name}_MOUNT_SCREW_{screw_index}",
                (x, y, 0.0228), 0.0020, 0.0010, steel, target, 16,
            )
            objects.append(screw)

    for string_id in geometry.string_ids_low_to_high:
        spec = geometry.strings[string_id]
        _nut, bridge_point = physical_nut_bridge(geometry, string_id)
        bridge = cube(
            f"V206_BRIDGE_{string_id}",
            (bridge_point.x + 0.014, spec.bridge_y_m, 0.022),
            (0.022, 0.0042, 0.010), black, target, 0.0018,
        )
        bridge["string_id"] = string_id
        bridge["scale_endpoint_x_m"] = bridge_point.x
        objects.append(bridge)
        saddle = cylinder(
            f"V206_SADDLE_{string_id}",
            (bridge_point.x, spec.bridge_y_m, 0.032), 0.0032, 0.0070, steel, target, 20,
        )
        saddle.rotation_euler.x = math.radians(90)
        objects.append(saddle)

    for index, (x, y) in enumerate(((0.790, -0.115), (0.858, -0.092)), 1):
        knob = cylinder(f"V206_CONTROL_KNOB_{index}", (x, y, 0.020), 0.0155, 0.018, black, target, 48)
        knob["control"] = "volume" if index == 1 else "tone"
        objects.append(knob)
    switch = cylinder("V206_CONTROL_SWITCH_BASE", (0.785, 0.105, 0.015), 0.0065, 0.010, black, target, 32)
    objects.append(switch)
    toggle = curve_segments(
        "V206_CONTROL_SWITCH_TOGGLE",
        [[(0.785, 0.105, 0.020), (0.798, 0.105, 0.047)]],
        0.0021, steel, target,
    )
    toggle["positions"] = 3
    objects.append(toggle)
    jack = cylinder("V206_OUTPUT_JACK", (0.914, -0.112, -0.002), 0.009, 0.006, steel, target, 32)
    jack["type"] = "quarter_inch_side_jack"
    objects.append(jack)
    for index, (x, y) in enumerate(((0.900, 0.145), (0.900, -0.155)), 1):
        button = cylinder(f"V206_STRAP_BUTTON_{index}", (x, y, -0.025), 0.006, 0.010, steel, target, 24)
        objects.append(button)
    return objects


def build_guitar() -> dict[str, object]:
    geometry = GuitarGeometry.from_mapping(load_authoritative_mapping())
    target = collection("V206_GUITAR_REBUILD")
    for obj in tuple(target.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    removed = remove_legacy_guitar()

    root = link_object("V206_GUITAR_ROOT", None, target)
    root.empty_display_type = "PLAIN_AXES"
    root["local_coordinate_system"] = "X nut-to-bridge, Y S1-to-S8, Z fretboard-front"
    local_x = Vector((0.819152, 0.0, 0.573576))
    local_y = Vector((-0.573576, 0.0, 0.819152))
    local_z = Vector((0.0, -1.0, 0.0))
    location = Vector((-0.570, -0.230, 1.090))
    root.matrix_world = Matrix((
        (local_x.x, local_y.x, local_z.x, location.x),
        (local_x.y, local_y.y, local_z.y, location.y),
        (local_x.z, local_y.z, local_z.z, location.z),
        (0.0, 0.0, 0.0, 1.0),
    ))

    materials = {
        "body": principled_material("MAT_V206_BODY_EDGE", (0.008, 0.010, 0.012, 1.0), 0.30),
        "top": figured_top_material(),
        "maple": maple_material(),
        "black": principled_material("MAT_V206_BLACK_HARDWARE", (0.006, 0.007, 0.008, 1.0), 0.24, 0.18, 0.35),
        "steel": principled_material("MAT_V206_BRUSHED_STEEL", (0.31, 0.33, 0.35, 1.0), 0.20, 0.94, 0.70),
        "inlay": principled_material("MAT_V206_INLAY", (0.70, 0.72, 0.69, 1.0), 0.18, 0.12),
    }
    built: list[bpy.types.Object] = [root]
    body = extruded_polygon("V206_BODY_CORE", BODY_OUTLINE, -0.047, -0.003, materials["body"], target, 0.008)
    body["construction"] = "compact_chambered_double_cut"
    built.append(body)
    top_outline = tuple((0.506 + (x - 0.506) * 0.972, y * 0.965) for x, y in BODY_OUTLINE)
    top = extruded_polygon("V206_FIGURED_TOP", top_outline, -0.003, 0.004, materials["top"], target, 0.004)
    top["finish"] = "smoky_charcoal_figured_satin"
    built.append(top)

    neck = tapered_prism("V206_NECK", -0.031, 0.605, 0.0330, 0.0475, -0.027, 0.008, materials["maple"], target, 0.003)
    neck["profile"] = "faceted_endurneck_inspired_no_branding"
    fretboard = tapered_prism("V206_FRETBOARD", -0.022, 0.563, 0.0310, 0.0445, 0.008, 0.0155, materials["maple"], target, 0.0012)
    fretboard["radius"] = "flat_multiscale"
    nut_low, _ = physical_nut_bridge(geometry, "S1")
    nut_high, _ = physical_nut_bridge(geometry, "S8")
    nut = curve_segments(
        "V206_HEADLESS_NUT",
        [[(nut_low.x, nut_low.y - 0.0035, 0.020), (nut_high.x, nut_high.y + 0.0035, 0.020)]],
        0.0028, materials["black"], target,
    )
    nut["headless"] = True
    terminal = cube("V206_HEADLESS_STRING_LOCK", (-0.025, 0.0, 0.010), (0.011, 0.036, 0.010), materials["black"], target, 0.002)
    terminal["headstock"] = False
    built.extend((neck, fretboard, nut, terminal))
    for string_id in geometry.string_ids_low_to_high:
        nut_point, _bridge_point = physical_nut_bridge(geometry, string_id)
        lock = cube(
            f"V206_NUT_LOCK_{string_id}",
            (nut_point.x - 0.007, nut_point.y, 0.023),
            (0.006, 0.0032, 0.0045), materials["black"], target, 0.001,
        )
        lock["string_id"] = string_id
        built.append(lock)

    fret_segments: list[list[tuple[float, float, float]]] = []
    for fret in range(1, geometry.fret_count + 1):
        low = physical_point(geometry, "S1", fret)
        high = physical_point(geometry, "S8", fret)
        direction = high - low
        direction.normalize()
        start = low - direction * 0.0035
        end = high + direction * 0.0035
        fret_segments.append([(start.x, start.y, 0.0190), (end.x, end.y, 0.0190)])
    frets = curve_segments("V206_FRETS", fret_segments, 0.00115, materials["steel"], target)
    frets["fret_count"] = geometry.fret_count
    frets["neutral_fret"] = geometry.neutral_fret
    frets["construction"] = "true_per_string_equal_temperament_fan"
    built.append(frets)

    string_objects = []
    for index, string_id in enumerate(geometry.string_ids_low_to_high):
        spec = geometry.strings[string_id]
        nut_point, bridge_point = physical_nut_bridge(geometry, string_id)
        last_fret = physical_point(geometry, string_id, geometry.fret_count)
        radius = STRING_GAUGES_IN[index] * 0.0254 * 0.5
        string = curve_segments(
            f"V206_STRING_{string_id}",
            [[
                (nut_point.x, spec.nut_y_m, 0.0211),
                (last_fret.x, last_fret.y, 0.0223),
                (bridge_point.x, spec.bridge_y_m, 0.0320),
            ]],
            radius, materials["steel"], target,
        )
        string["string_id"] = string_id
        string["tuning"] = spec.tuning
        string["scale_m"] = spec.scale_m
        string["physical_nut_x_m"] = nut_point.x
        string["physical_bridge_x_m"] = bridge_point.x
        string["nut_y_m"] = spec.nut_y_m
        string["bridge_y_m"] = spec.bridge_y_m
        string["gauge_in"] = STRING_GAUGES_IN[index]
        string_objects.append(string)
    built.extend(string_objects)

    for fret in (3, 5, 7, 9, 12, 15, 17, 19, 21, 24):
        low = physical_point(geometry, "S1", fret)
        high = physical_point(geometry, "S8", fret)
        prior_low = physical_point(geometry, "S1", fret - 1)
        prior_high = physical_point(geometry, "S8", fret - 1)
        center = (low + high + prior_low + prior_high) * 0.25
        offsets = (-0.008, 0.008) if fret == 12 else (0.0,)
        for dot_index, offset in enumerate(offsets, 1):
            dot = cylinder(f"V206_INLAY_F{fret}_{dot_index}", (center.x, offset, 0.0166), 0.0028, 0.0010, materials["inlay"], target, 24)
            dot["fret"] = fret
            built.append(dot)

    built.extend(add_hardware(target, geometry, materials))
    rear_plate = extruded_polygon(
        "V206_REAR_ELECTRONICS_COVER",
        ((0.704, -0.028), (0.825, -0.054), (0.872, -0.128), (0.750, -0.142), (0.688, -0.090)),
        -0.0492, -0.0472, materials["black"], target, 0.002,
    )
    rear_plate["service_access"] = "controls_and_output_jack"
    built.append(rear_plate)
    for index, (x, y) in enumerate(((0.708, -0.044), (0.814, -0.064), (0.850, -0.119), (0.747, -0.129)), 1):
        screw = cylinder(f"V206_REAR_COVER_SCREW_{index}", (x, y, -0.0500), 0.0018, 0.0008, materials["steel"], target, 16)
        built.append(screw)
    parent_to_root(built, root)
    root["string_count"] = 8
    root["fret_count"] = 24
    root["neutral_fret"] = 7
    root["neutral_fret_x_m"] = NEUTRAL_FRET_X
    root["nut_string_spread_m"] = 0.049
    root["bridge_string_spread_m"] = 0.0735
    root["body_length_m"] = max(x for x, _ in BODY_OUTLINE) - min(x for x, _ in BODY_OUTLINE)
    root["body_width_m"] = max(y for _, y in BODY_OUTLINE) - min(y for _, y in BODY_OUTLINE)
    return {
        "root": root,
        "geometry": geometry,
        "legacy_removed": removed,
        "objects": built,
        "materials": materials,
    }


def look_at(obj: bpy.types.Object, target: tuple[float, float, float]) -> None:
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def add_camera(name: str, location: tuple[float, float, float], target: tuple[float, float, float], ortho: float | None, lens: float, target_collection: bpy.types.Collection) -> bpy.types.Object:
    data = bpy.data.cameras.new(f"{name}_DATA")
    data.lens = lens
    if ortho is not None:
        data.type = "ORTHO"
        data.ortho_scale = ortho
    obj = link_object(name, data, target_collection)
    obj.location = location
    look_at(obj, target)
    return obj


def add_light(name: str, location: tuple[float, float, float], energy: float, size: float, target_collection: bpy.types.Collection) -> bpy.types.Object:
    data = bpy.data.lights.new(f"{name}_DATA", "AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size
    obj = link_object(name, data, target_collection)
    obj.location = location
    look_at(obj, (0.55, 0.0, 0.0))
    return obj


def create_render_rig(target: bpy.types.Collection) -> None:
    for name in list(RENDER_VIEWS):
        old = bpy.data.objects.get(RENDER_VIEWS[name][0])
        if old:
            bpy.data.objects.remove(old, do_unlink=True)
    add_camera("V206_CAM_FRONT", (0.48, 0.0, 1.55), (0.48, 0.0, 0.0), 1.12, 90, target)
    add_camera("V206_CAM_BACK", (0.48, 0.0, -1.55), (0.48, 0.0, -0.02), 1.12, 90, target)
    add_camera("V206_CAM_BEAUTY", (0.92, -1.10, 0.80), (0.52, 0.0, 0.0), None, 72, target)
    add_camera("V206_CAM_BRIDGE", (0.70, -0.42, 0.38), (0.69, 0.0, 0.02), None, 110, target)
    add_camera("V206_CAM_CONTROLS", (0.88, -0.44, 0.38), (0.82, -0.04, 0.02), None, 110, target)
    add_camera("V206_CAM_FRETBOARD", (0.28, -0.42, 0.34), (0.28, 0.0, 0.015), None, 105, target)
    for name in ("V206_KEY", "V206_FILL", "V206_RIM"):
        old = bpy.data.objects.get(name)
        if old:
            bpy.data.objects.remove(old, do_unlink=True)
    add_light("V206_KEY", (0.30, -0.75, 1.20), 450.0, 0.75, target)
    add_light("V206_FILL", (1.05, 0.60, 0.85), 120.0, 0.60, target)
    add_light("V206_RIM", (0.40, 0.45, -0.75), 300.0, 0.45, target)


def render_acceptance(root: bpy.types.Object) -> dict[str, object]:
    scene = bpy.context.scene
    render_dir = STAGE / "renders" / "guitar"
    render_dir.mkdir(parents=True, exist_ok=True)
    previous_matrix = root.matrix_world.copy()
    previous_visibility = {obj.name: obj.hide_render for obj in bpy.data.objects}
    root.matrix_world = Matrix.Identity(4)
    for obj in bpy.data.objects:
        if not obj.name.startswith("V206_"):
            obj.hide_render = True
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 48
    scene.cycles.use_denoising = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = False
    scene.render.image_settings.color_depth = "8"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.view_settings.exposure = -1.8
    scene.world.use_nodes = True
    background = scene.world.node_tree.nodes.get("Background")
    if background is not None:
        background.inputs["Color"].default_value = (0.008, 0.010, 0.014, 1.0)
        background.inputs["Strength"].default_value = 0.12
    manifest: dict[str, object] = {"renderer": "Cycles CPU", "renders": {}}
    try:
        for key, (camera_name, resolution, lighting) in RENDER_VIEWS.items():
            scene.camera = bpy.data.objects[camera_name]
            scene.render.resolution_x, scene.render.resolution_y = resolution
            scene.render.resolution_percentage = 100
            output = render_dir / f"{key}.png"
            scene.render.filepath = str(output)
            bpy.ops.render.render(write_still=True)
            manifest["renders"][key] = {
                "path": str(output.relative_to(ROOT)),
                "sha256": sha256(output),
                "resolution": list(resolution),
                "lighting": lighting,
                "renderer": "Cycles CPU",
            }
    finally:
        root.matrix_world = previous_matrix
        for name, hidden in previous_visibility.items():
            obj = bpy.data.objects.get(name)
            if obj:
                obj.hide_render = hidden
    write_json(STAGE / "audit" / "v206_render_manifest.json", manifest)
    return manifest


def main() -> None:
    require(EXPECTED_SOURCE_SHA256 != "__V205_SOURCE_SHA256__", "Inject accepted V205 SHA-256 before running V206")
    require(Path(bpy.data.filepath).resolve() == SOURCE.resolve(), f"Open accepted V205 source first: {SOURCE}")
    require(sha256(SOURCE) == EXPECTED_SOURCE_SHA256, "Accepted V205 source hash changed")
    require(sha256(ROOT / "ant_character_asset_final_v200.blend") == EXPECTED_V200_SHA256, "Protected V200 changed")
    require(sha256(ROOT / "ant_compact_pick_pinch_v192.blend") == EXPECTED_V192_SHA256, "Protected V192 changed")
    STAGE.joinpath("audit").mkdir(parents=True, exist_ok=True)
    result = build_guitar()
    create_render_rig(collection("V206_GUITAR_REBUILD"))
    geometry: GuitarGeometry = result["geometry"]
    scene = bpy.context.scene
    scene["checkpoint"] = "V206_GUITAR"
    scene["source_v205_sha256"] = EXPECTED_SOURCE_SHA256
    scene["reference_authority"] = "supplied guitar sheets > analytic M3 geometry > generated interpretation aid"
    scene["v206_instrument_type"] = "headless_eight_string_multiscale"
    scene["v206_string_order"] = json.dumps(list(geometry.string_ids_low_to_high))
    scene["v206_tuning_low_to_high"] = json.dumps([geometry.strings[name].tuning for name in geometry.string_ids_low_to_high])
    scene["v206_scale_lengths_m"] = json.dumps({name: geometry.strings[name].scale_m for name in geometry.string_ids_low_to_high}, sort_keys=True)
    scene["v206_geometry_mapping_sha256"] = sha256(ROOT / "references" / "m3" / "m3_chord_mapping_v2.json")
    audit = {
        "schema": "v206-guitar-build-v1",
        "authority": "supplied",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": EXPECTED_SOURCE_SHA256},
        "instrument": {
            "type": "compact headless eight-string multiscale electric guitar",
            "strings": 8,
            "frets": 24,
            "neutral_fret": 7,
            "neutral_fret_x_m": NEUTRAL_FRET_X,
            "nut_spread_m": 0.049,
            "bridge_spread_m": 0.0735,
            "string_order_low_to_high": list(geometry.string_ids_low_to_high),
            "tuning_low_to_high": [geometry.strings[name].tuning for name in geometry.string_ids_low_to_high],
            "scale_lengths_m": {name: geometry.strings[name].scale_m for name in geometry.string_ids_low_to_high},
            "gauges_in": dict(zip(geometry.string_ids_low_to_high, STRING_GAUGES_IN)),
        },
        "construction": {
            "body": "compact ergonomic double-cut, figured charcoal top, dark edge/back",
            "neck": "headless roasted-maple faceted neck with flat multiscale board",
            "pickups": 2,
            "bridge_tuners": 8,
            "controls": {"knobs": 2, "switches": 1},
            "legacy_objects_removed": result["legacy_removed"],
        },
        "object_count": len([obj for obj in bpy.data.objects if obj.name.startswith("V206_")]),
        "protected_hashes": {"V200": EXPECTED_V200_SHA256, "V192": EXPECTED_V192_SHA256},
    }
    write_json(STAGE / "audit" / "v206_guitar_audit.json", audit)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    output_hash = sha256(OUTPUT)
    write_json(
        STAGE / "audit" / "v206_build_receipt.json",
        {
            "status": "PASS",
            "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": EXPECTED_SOURCE_SHA256},
            "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": output_hash},
            "guitar_audit_sha256": sha256(STAGE / "audit" / "v206_guitar_audit.json"),
        },
    )
    render_acceptance(result["root"])
    print(f"V206_GUITAR_BUILD_OK output_sha256={output_hash} strings=8 frets=24")


if __name__ == "__main__":
    main()
