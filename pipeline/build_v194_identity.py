from __future__ import annotations

import argparse
import bmesh
import hashlib
import json
import math
import random
import sys
from pathlib import Path

import bpy
from mathutils import Vector


STAGE_ROOT = Path(__file__).resolve().parents[1]
if str(STAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(STAGE_ROOT))

from pipeline.common import ensure_material, link_object_like, sha256, snapshot_objects, write_json
from pipeline.rendering import BODY_CAMERAS, HEAD_CAMERAS, render_group


BODY_NAME = "V163_BODY_FAILED_PICKING_HAND_MASKED"
HAIR_NAME = "V131_CLEAN_CONNECTED_SHORT_CURL_HAIR"
NECK_LOCK_Z = 1.48
HEAD_CENTER = Vector((0.0, -0.002, 1.689))
HEAD_RADII = Vector((0.097, 0.086, 0.126))


def activate(obj: bpy.types.Object) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def smooth(obj: bpy.types.Object) -> None:
    if obj.type == "MESH":
        for polygon in obj.data.polygons:
            polygon.use_smooth = True


def apply_scale(obj: bpy.types.Object) -> None:
    activate(obj)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)


def assign_material(obj: bpy.types.Object, material: bpy.types.Material) -> None:
    obj.data.materials.clear()
    obj.data.materials.append(material)


def make_materials() -> dict[str, bpy.types.Material]:
    skin = ensure_material("V194_SKIN_MAT", (0.17, 0.055, 0.020, 1.0), 0.62)
    sclera = ensure_material("V194_WARM_SCLERA_MAT", (0.34, 0.29, 0.22, 1.0), 0.48)
    iris = ensure_material("V194_DEEP_BROWN_IRIS_MAT", (0.038, 0.012, 0.003, 1.0), 0.42)
    pupil = ensure_material("V194_PUPIL_MAT", (0.003, 0.002, 0.001, 1.0), 0.3)
    lip = ensure_material("V194_NATURAL_LIP_MAT", (0.115, 0.025, 0.014, 1.0), 0.58)
    line = ensure_material("V194_FEATURE_LINE_MAT", (0.018, 0.006, 0.003, 1.0), 0.72)
    beard = ensure_material("V194_CLOSE_BEARD_MAT", (0.030, 0.010, 0.004, 1.0), 0.86)
    hair = ensure_material("V194_DENSE_CURL_HAIR_MAT", (0.002, 0.0015, 0.001, 1.0), 0.88)

    for material, specular in ((skin, 0.28), (sclera, 0.34), (beard, 0.12), (hair, 0.10), (lip, 0.24)):
        principled_node = material.node_tree.nodes.get("Principled BSDF") if material.use_nodes else None
        if principled_node:
            if "Specular IOR Level" in principled_node.inputs:
                principled_node.inputs["Specular IOR Level"].default_value = specular

    nodes = hair.node_tree.nodes
    links = hair.node_tree.links
    principled = nodes.get("Principled BSDF")
    if principled and not nodes.get("V194 Curl Noise"):
        noise = nodes.new("ShaderNodeTexNoise")
        noise.name = "V194 Curl Noise"
        noise.inputs["Scale"].default_value = 135.0
        noise.inputs["Detail"].default_value = 7.0
        noise.inputs["Roughness"].default_value = 0.72
        ramp = nodes.new("ShaderNodeValToRGB")
        ramp.name = "V194 Curl Color"
        ramp.color_ramp.elements[0].color = (0.0002, 0.00015, 0.0001, 1.0)
        ramp.color_ramp.elements[1].color = (0.006, 0.0035, 0.0018, 1.0)
        bump = nodes.new("ShaderNodeBump")
        bump.name = "V194 Curl Bump"
        bump.inputs["Strength"].default_value = 0.34
        bump.inputs["Distance"].default_value = 0.010
        links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
        links.new(ramp.outputs["Color"], principled.inputs["Base Color"])
        links.new(noise.outputs["Fac"], bump.inputs["Height"])
        links.new(bump.outputs["Normal"], principled.inputs["Normal"])
    beard_nodes = beard.node_tree.nodes
    beard_links = beard.node_tree.links
    beard_principled = beard_nodes.get("Principled BSDF")
    if beard_principled and not beard_nodes.get("V194 Stubble Noise"):
        noise = beard_nodes.new("ShaderNodeTexNoise")
        noise.name = "V194 Stubble Noise"
        noise.inputs["Scale"].default_value = 170.0
        noise.inputs["Detail"].default_value = 4.0
        ramp = beard_nodes.new("ShaderNodeValToRGB")
        ramp.name = "V194 Stubble Color"
        ramp.color_ramp.elements[0].color = (0.010, 0.003, 0.001, 1.0)
        ramp.color_ramp.elements[1].color = (0.055, 0.020, 0.007, 1.0)
        bump = beard_nodes.new("ShaderNodeBump")
        bump.name = "V194 Stubble Bump"
        bump.inputs["Strength"].default_value = 0.22
        bump.inputs["Distance"].default_value = 0.004
        beard_links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
        beard_links.new(ramp.outputs["Color"], beard_principled.inputs["Base Color"])
        beard_links.new(noise.outputs["Fac"], bump.inputs["Height"])
        beard_links.new(bump.outputs["Normal"], beard_principled.inputs["Normal"])
    return {
        "skin": skin,
        "sclera": sclera,
        "iris": iris,
        "pupil": pupil,
        "lip": lip,
        "line": line,
        "beard": beard,
        "hair": hair,
    }


def coords_hash(coords: list[tuple[float, float, float]]) -> str:
    payload = json.dumps(sorted(tuple(round(value, 7) for value in item) for item in coords), separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def replace_body_above_neck() -> tuple[bpy.types.Object, dict[str, object]]:
    source = bpy.data.objects.get(BODY_NAME)
    if source is None or source.type != "MESH":
        raise RuntimeError(f"Missing body target: {BODY_NAME}")
    before_coords = [tuple(vertex.co) for vertex in source.data.vertices if vertex.co.z <= NECK_LOCK_Z]
    duplicate = source.copy()
    duplicate.data = source.data.copy()
    duplicate.name = "V194_BODY_IDENTITY_BASE"
    link_object_like(source, duplicate)

    mesh = bmesh.new()
    mesh.from_mesh(duplicate.data)
    mesh.verts.ensure_lookup_table()
    bmesh.ops.delete(mesh, geom=[vertex for vertex in mesh.verts if vertex.co.z > NECK_LOCK_Z], context="VERTS")
    mesh.to_mesh(duplicate.data)
    mesh.free()
    duplicate.data.update()
    after_coords = [tuple(vertex.co) for vertex in duplicate.data.vertices]
    before_hash = coords_hash(before_coords)
    after_hash = coords_hash(after_coords)
    if len(before_coords) != len(after_coords) or before_hash != after_hash:
        raise RuntimeError("Below-neck vertex lock changed while removing the predecessor head")
    source.hide_render = True
    source.hide_viewport = True
    return duplicate, {"z_lock": NECK_LOCK_Z, "count": len(after_coords), "before": before_hash, "after": after_hash}


def add_uv_sphere(
    name: str,
    location: tuple[float, float, float],
    scale: tuple[float, float, float],
    material: bpy.types.Material,
    segments: int = 48,
    rings: int = 24,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    apply_scale(obj)
    assign_material(obj, material)
    smooth(obj)
    return obj


def make_curve(
    name: str,
    points: list[tuple[float, float, float]],
    bevel_depth: float,
    material: bpy.types.Material,
    cyclic: bool = False,
) -> bpy.types.Object:
    curve = bpy.data.curves.new(name + "_DATA", "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 2
    curve.bevel_depth = bevel_depth
    curve.bevel_resolution = 3
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for control, coordinate in zip(spline.bezier_points, points):
        control.co = coordinate
        control.handle_left_type = "AUTO"
        control.handle_right_type = "AUTO"
    spline.use_cyclic_u = cyclic
    obj = bpy.data.objects.new(name, curve)
    bpy.context.scene.collection.objects.link(obj)
    curve.materials.append(material)
    return obj


def build_head(materials: dict[str, bpy.types.Material]) -> tuple[bpy.types.Object, bpy.types.Object]:
    head = add_uv_sphere("V194_HEAD", tuple(HEAD_CENTER), tuple(HEAD_RADII), materials["skin"], 128, 72)
    for vertex in head.data.vertices:
        normalized_z = max(-1.0, min(1.0, vertex.co.z / HEAD_RADII.z))
        if normalized_z < -0.08:
            lower = (-normalized_z - 0.08) / 0.92
            vertex.co.x *= 1.0 - 0.065 * lower**1.8
            if vertex.co.y < 0:
                vertex.co.y -= 0.0045 * lower
        elif -0.08 <= normalized_z <= 0.32:
            vertex.co.x *= 1.025
        if normalized_z > 0.62:
            vertex.co.x *= 1.0 - 0.018 * ((normalized_z - 0.62) / 0.38)
        if vertex.co.y > 0:
            vertex.co.y *= 1.045
        elif normalized_z > 0.45:
            vertex.co.y *= 0.965
    head.data.update()

    beard = head.copy()
    beard.data = head.data.copy()
    beard.name = "V194_BEARD"
    bpy.context.scene.collection.objects.link(beard)
    beard_mesh = bmesh.new()
    beard_mesh.from_mesh(beard.data)
    beard_mesh.verts.ensure_lookup_table()
    remove = []
    for vertex in beard_mesh.verts:
        world = beard.location + vertex.co
        side_factor = min(1.0, abs(world.x) / 0.085)
        upper = 1.650 + 0.034 * side_factor
        mouth_clear = abs(world.x) < 0.042 and 1.598 < world.z < 1.641 and world.y < -0.042
        keep = 1.558 < world.z < upper and world.y < 0.027 and not mouth_clear
        if not keep:
            remove.append(vertex)
        else:
            vertex.co *= 1.0018
    bmesh.ops.delete(beard_mesh, geom=remove, context="VERTS")
    beard_mesh.to_mesh(beard.data)
    beard_mesh.free()
    assign_material(beard, materials["beard"])
    smooth(beard)

    bpy.ops.mesh.primitive_cone_add(
        vertices=64,
        radius1=0.071,
        radius2=0.061,
        depth=0.128,
        location=(0.0, 0.006, 1.528),
    )
    neck = bpy.context.object
    neck.name = "V194_NECK_COMPONENT"
    neck.scale = (1.0, 0.91, 1.0)
    apply_scale(neck)
    assign_material(neck, materials["skin"])
    smooth(neck)
    bevel = neck.modifiers.new("V194 Neck Soft Edge", "BEVEL")
    bevel.width = 0.005
    bevel.segments = 4
    activate(neck)
    bpy.ops.object.modifier_apply(modifier=bevel.name)

    bpy.ops.object.select_all(action="DESELECT")
    head.select_set(True)
    neck.select_set(True)
    bpy.context.view_layer.objects.active = head
    bpy.ops.object.join()
    head.name = "V194_HEAD"
    smooth(head)
    return head, beard


def build_nose(materials: dict[str, bpy.types.Material]) -> list[bpy.types.Object]:
    rings = [
        (1.728, -0.080, 0.0080, 0.0045),
        (1.701, -0.086, 0.0095, 0.0055),
        (1.674, -0.094, 0.0115, 0.0065),
        (1.653, -0.103, 0.0140, 0.0080),
        (1.642, -0.106, 0.0170, 0.0090),
    ]
    segments = 20
    vertices = []
    for z, center_y, radius_x, radius_y in rings:
        for index in range(segments):
            angle = 2.0 * math.pi * index / segments
            vertices.append((radius_x * math.cos(angle), center_y + radius_y * math.sin(angle), z))
    faces = []
    for row in range(len(rings) - 1):
        for index in range(segments):
            next_index = (index + 1) % segments
            a = row * segments + index
            b = row * segments + next_index
            c = (row + 1) * segments + next_index
            d = (row + 1) * segments + index
            faces.append((a, b, c, d))
    faces.append(tuple(range(segments - 1, -1, -1)))
    start = (len(rings) - 1) * segments
    faces.append(tuple(start + index for index in range(segments)))
    mesh = bpy.data.meshes.new("V194_NOSE_DATA")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    nose = bpy.data.objects.new("V194_NOSE", mesh)
    bpy.context.scene.collection.objects.link(nose)
    assign_material(nose, materials["skin"])
    smooth(nose)
    left = add_uv_sphere("V194_NOSE_WING_L", (0.014, -0.103, 1.645), (0.013, 0.0080, 0.0075), materials["skin"], 40, 20)
    right = add_uv_sphere("V194_NOSE_WING_R", (-0.014, -0.103, 1.645), (0.013, 0.0080, 0.0075), materials["skin"], 40, 20)
    nostril_left = make_curve(
        "V194_NOSTRIL_L",
        [(0.006, -0.1120, 1.641), (0.013, -0.1135, 1.640), (0.020, -0.1105, 1.642)],
        0.00085,
        materials["line"],
    )
    nostril_right = make_curve(
        "V194_NOSTRIL_R",
        [(-0.020, -0.1105, 1.642), (-0.013, -0.1135, 1.640), (-0.006, -0.1120, 1.641)],
        0.00085,
        materials["line"],
    )
    return [nose, left, right, nostril_left, nostril_right]


def build_eyes(materials: dict[str, bpy.types.Material]) -> list[bpy.types.Object]:
    created = []
    gaze_shift = 0.0028
    for suffix, x in (("L", 0.033), ("R", -0.033)):
        eye = add_uv_sphere(f"V194_EYE_{suffix}", (x, -0.0805, 1.704), (0.0205, 0.0100, 0.0078), materials["sclera"], 48, 24)
        iris = add_uv_sphere(
            f"V194_IRIS_{suffix}",
            (x + gaze_shift, -0.0897, 1.703),
            (0.0052, 0.0017, 0.0052),
            materials["iris"],
            32,
            16,
        )
        pupil = add_uv_sphere(
            f"V194_PUPIL_{suffix}",
            (x + gaze_shift, -0.0911, 1.703),
            (0.0023, 0.0010, 0.0023),
            materials["pupil"],
            24,
            12,
        )
        upper_points = []
        lower_points = []
        for index in range(9):
            t = -1.0 + 2.0 * index / 8.0
            px = x + 0.020 * t
            upper_points.append((px, -0.0919, 1.704 + 0.0045 * (1.0 - t * t)))
            lower_points.append((px, -0.0915, 1.703 - 0.0031 * (1.0 - t * t)))
        upper = make_curve(f"V194_UPPER_LID_{suffix}", upper_points, 0.00145, materials["skin"])
        lower = make_curve(f"V194_LOWER_LID_{suffix}", lower_points, 0.00105, materials["skin"])
        brow_z = 1.733 if suffix == "L" else 1.731
        brow = make_curve(
            f"V194_BROW_{suffix}",
            [
                (x - 0.025, -0.0870, brow_z - 0.001),
                (x - 0.010, -0.0910, brow_z + 0.003),
                (x + 0.008, -0.0915, brow_z + 0.004),
                (x + 0.026, -0.0865, brow_z),
            ],
            0.0031,
            materials["line"],
        )
        created.extend([eye, iris, pupil, upper, lower, brow])
    dot = add_uv_sphere("V194_BROW_DOT", (0.0, -0.0885, 1.731), (0.0024, 0.0013, 0.0024), materials["line"], 20, 10)
    created.append(dot)
    return created


def build_mouth_and_facial_hair(materials: dict[str, bpy.types.Material]) -> list[bpy.types.Object]:
    upper = add_uv_sphere("V194_MOUTH", (0.0, -0.0735, 1.617), (0.027, 0.0063, 0.0042), materials["lip"], 48, 24)
    lower = add_uv_sphere("V194_LOWER_LIP_COMPONENT", (0.0, -0.0738, 1.610), (0.025, 0.0068, 0.0046), materials["lip"], 48, 24)
    bpy.ops.object.select_all(action="DESELECT")
    upper.select_set(True)
    lower.select_set(True)
    bpy.context.view_layer.objects.active = upper
    bpy.ops.object.join()
    upper.name = "V194_MOUTH"
    mouth_line = make_curve(
        "V194_MOUTH_LINE",
        [(-0.026, -0.0800, 1.614), (-0.013, -0.0808, 1.6135), (0.0, -0.0810, 1.6135), (0.013, -0.0808, 1.6135), (0.026, -0.0800, 1.614)],
        0.0008,
        materials["line"],
    )
    mustache_left = make_curve(
        "V194_MUSTACHE_L",
        [(0.0045, -0.0803, 1.630), (0.013, -0.0820, 1.633), (0.024, -0.0810, 1.630), (0.033, -0.0780, 1.626)],
        0.0024,
        materials["beard"],
    )
    mustache_right = make_curve(
        "V194_MUSTACHE_R",
        [(-0.033, -0.0780, 1.626), (-0.024, -0.0810, 1.630), (-0.013, -0.0820, 1.633), (-0.0045, -0.0803, 1.630)],
        0.0024,
        materials["beard"],
    )
    soul_patch = make_curve(
        "V194_SOUL_PATCH",
        [(-0.006, -0.0750, 1.599), (0.0, -0.0765, 1.594), (0.006, -0.0750, 1.599)],
        0.0017,
        materials["beard"],
    )
    return [upper, mouth_line, mustache_left, mustache_right, soul_patch]


def build_ears(materials: dict[str, bpy.types.Material]) -> list[bpy.types.Object]:
    created = []
    for suffix, x, sign in (("L", 0.099, 1.0), ("R", -0.099, -1.0)):
        ear = add_uv_sphere(f"V194_EAR_{suffix}", (x, -0.001, 1.677), (0.0125, 0.0090, 0.026), materials["skin"], 48, 28)
        crease = make_curve(
            f"V194_EAR_CREASE_{suffix}",
            [
                (x - sign * 0.002, -0.0110, 1.693),
                (x + sign * 0.005, -0.0120, 1.682),
                (x + sign * 0.003, -0.0120, 1.666),
                (x - sign * 0.003, -0.0105, 1.662),
            ],
            0.00135,
            materials["line"],
        )
        created.extend([ear, crease])
    return created


def build_hair(materials: dict[str, bpy.types.Material]) -> list[bpy.types.Object]:
    hair = add_uv_sphere(
        "V194_HAIR",
        tuple(HEAD_CENTER + Vector((0.0, 0.003, 0.005))),
        (HEAD_RADII.x * 1.055, HEAD_RADII.y * 1.065, HEAD_RADII.z * 1.045),
        materials["hair"],
        128,
        72,
    )
    hair_mesh = bmesh.new()
    hair_mesh.from_mesh(hair.data)
    hair_mesh.verts.ensure_lookup_table()
    remove = []
    for vertex in hair_mesh.verts:
        local = vertex.co
        world = hair.location + local
        phi = math.atan2(local.y / (HEAD_RADII.y * 1.065), local.x / (HEAD_RADII.x * 1.055))
        frontness = max(0.0, -math.sin(phi))
        backness = max(0.0, math.sin(phi))
        theta_max = 1.34 - 0.20 * frontness + 0.23 * backness
        normalized_z = max(-1.0, min(1.0, local.z / (HEAD_RADII.z * 1.045)))
        theta = math.acos(normalized_z)
        part_x = 0.036 + 0.20 * (world.z - 1.75)
        in_part = world.y < -0.025 and 1.744 < world.z < 1.796 and abs(world.x - part_x) < 0.0032
        if theta > theta_max or in_part:
            remove.append(vertex)
    bmesh.ops.delete(hair_mesh, geom=remove, context="VERTS")
    hair_mesh.to_mesh(hair.data)
    hair_mesh.free()
    hair.data.update()
    smooth(hair)

    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, int, int, int]] = []
    rng = random.Random(194)
    rows = [(0.20, 8), (0.36, 12), (0.52, 16), (0.68, 20), (0.84, 24), (1.00, 28), (1.16, 30), (1.32, 30), (1.46, 28)]

    def append_clump(
        center: Vector,
        tangent_a: Vector,
        tangent_b: Vector,
        normal: Vector,
        radius_a: float,
        radius_b: float,
        radius_n: float,
    ) -> None:
        longitude_count = 8
        latitude_rings = 4
        top = len(vertices)
        vertices.append(tuple(center + normal * radius_n))
        ring_starts = []
        for ring in range(1, latitude_rings + 1):
            latitude = math.pi * ring / (latitude_rings + 1)
            ring_starts.append(len(vertices))
            for longitude in range(longitude_count):
                angle = 2.0 * math.pi * longitude / longitude_count
                point = (
                    center
                    + tangent_a * (radius_a * math.sin(latitude) * math.cos(angle))
                    + tangent_b * (radius_b * math.sin(latitude) * math.sin(angle))
                    + normal * (radius_n * math.cos(latitude))
                )
                vertices.append(tuple(point))
        bottom = len(vertices)
        vertices.append(tuple(center - normal * radius_n))
        first = ring_starts[0]
        for longitude in range(longitude_count):
            next_longitude = (longitude + 1) % longitude_count
            faces.append((top, first + longitude, first + next_longitude))
        for ring in range(latitude_rings - 1):
            start = ring_starts[ring]
            next_start = ring_starts[ring + 1]
            for longitude in range(longitude_count):
                next_longitude = (longitude + 1) % longitude_count
                faces.append(
                    (
                        start + longitude,
                        next_start + longitude,
                        next_start + next_longitude,
                        start + next_longitude,
                    )
                )
        last = ring_starts[-1]
        for longitude in range(longitude_count):
            next_longitude = (longitude + 1) % longitude_count
            faces.append((last + next_longitude, last + longitude, bottom))

    for row_index, (theta_base, count) in enumerate(rows):
        for item_index in range(count):
            phi = 2.0 * math.pi * (item_index + 0.5 * (row_index % 2)) / count + rng.uniform(-0.045, 0.045)
            theta = theta_base + rng.uniform(-0.025, 0.025)
            local = Vector(
                (
                    HEAD_RADII.x * 1.06 * math.sin(theta) * math.cos(phi),
                    HEAD_RADII.y * 1.07 * math.sin(theta) * math.sin(phi),
                    HEAD_RADII.z * 1.05 * math.cos(theta),
                )
            )
            center = HEAD_CENTER + Vector((0.0, 0.003, 0.005)) + local
            frontness = max(0.0, -math.sin(phi))
            backness = max(0.0, math.sin(phi))
            theta_max = 1.34 - 0.20 * frontness + 0.23 * backness
            part_x = 0.036 + 0.20 * (center.z - 1.75)
            if theta > theta_max or (
                center.y < -0.020
                and 1.740 < center.z < 1.800
                and abs(center.x - part_x) < 0.009
            ):
                continue
            normal = Vector(
                (
                    local.x / (HEAD_RADII.x**2),
                    local.y / (HEAD_RADII.y**2),
                    local.z / (HEAD_RADII.z**2),
                )
            ).normalized()
            tangent_a = normal.cross(Vector((0.0, 0.0, 1.0)))
            if tangent_a.length < 0.1:
                tangent_a = normal.cross(Vector((0.0, 1.0, 0.0)))
            tangent_a.normalize()
            tangent_b = normal.cross(tangent_a).normalized()
            center += normal * 0.0025
            append_clump(
                center,
                tangent_a,
                tangent_b,
                normal,
                0.0060 + rng.uniform(-0.0006, 0.0006),
                0.0045 + rng.uniform(-0.0005, 0.0005),
                0.0030 + rng.uniform(-0.0003, 0.0003),
            )
    curl_mesh = bpy.data.meshes.new("V194_HAIR_CURL_DETAIL_DATA")
    curl_mesh.from_pydata(vertices, [], faces)
    curl_mesh.update()
    curls = bpy.data.objects.new("V194_HAIR_CURL_DETAIL", curl_mesh)
    bpy.context.scene.collection.objects.link(curls)
    assign_material(curls, materials["hair"])
    smooth(curls)
    return [hair, curls]


def world_bounds(obj: bpy.types.Object) -> dict[str, list[float]]:
    corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    return {
        "min": [round(min(point[index] for point in corners), 6) for index in range(3)],
        "max": [round(max(point[index] for point in corners), 6) for index in range(3)],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--stage-root", type=Path, default=STAGE_ROOT)
    return parser.parse_args(sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else [])


def main() -> None:
    args = parse_args()
    source = args.source.resolve()
    output = args.output.resolve()
    stage_root = args.stage_root.resolve()
    if Path(bpy.data.filepath).resolve() != source:
        raise RuntimeError(f"Loaded source mismatch: {bpy.data.filepath} != {source}")
    output.parent.mkdir(parents=True, exist_ok=True)
    for obj in list(bpy.data.objects):
        if obj.name.startswith("V194_"):
            bpy.data.objects.remove(obj, do_unlink=True)

    excluded = {BODY_NAME, HAIR_NAME}
    protected_before = snapshot_objects(excluded=excluded, excluded_prefixes=("V194_",))
    materials = make_materials()
    body, below_neck = replace_body_above_neck()
    predecessor_hair = bpy.data.objects.get(HAIR_NAME)
    if predecessor_hair is None:
        raise RuntimeError(f"Missing hair target: {HAIR_NAME}")
    predecessor_hair.hide_render = True
    predecessor_hair.hide_viewport = True

    created: list[bpy.types.Object] = [body]
    head, beard = build_head(materials)
    created.extend([head, beard])
    created.extend(build_nose(materials))
    created.extend(build_eyes(materials))
    created.extend(build_mouth_and_facial_hair(materials))
    created.extend(build_ears(materials))
    created.extend(build_hair(materials))
    protected_after = snapshot_objects(excluded=excluded, excluded_prefixes=("V194_",))
    if protected_before != protected_after:
        raise RuntimeError(f"Protected scene changed: {protected_before} != {protected_after}")

    scene = bpy.context.scene
    scene["checkpoint"] = "V194"
    scene["checkpoint_intent"] = "reference-aligned adult identity head, neck, ears, facial features, facial hair, and single-left-part curls"
    scene["source_checkpoint"] = source.name
    scene["reference_contract"] = "character-reference-contract-v1"
    bpy.ops.wm.save_as_mainfile(filepath=str(output), check_existing=False)

    production = stage_root / "production_v194_identity"
    render_dir = production / "renders" / "head_v194"
    outputs = render_group(output, render_dir, HEAD_CAMERAS, (720, 720))
    context_outputs = render_group(output, render_dir, {"context_front": BODY_CAMERAS["front"]}, (720, 900))
    output_paths = {**outputs, **context_outputs}
    landmarks = {
        "head": world_bounds(head),
        "ear_l": world_bounds(bpy.data.objects["V194_EAR_L"]),
        "ear_r": world_bounds(bpy.data.objects["V194_EAR_R"]),
        "hair": world_bounds(bpy.data.objects["V194_HAIR"]),
        "eyes_z": 1.704,
        "nose_base_z": 1.642,
        "mouth_z": 1.613,
        "hair_part": {"side": "anatomical_left", "world_x": 0.035, "count": 1},
    }
    audit_path = production / "audit" / "v194_identity_audit.json"
    render_manifest = {
        label: {
            "camera": ({**HEAD_CAMERAS, "context_front": BODY_CAMERAS["front"]})[label],
            "path": str(Path(path).relative_to(stage_root)),
            "sha256": sha256(Path(path)),
        }
        for label, path in output_paths.items()
    }
    write_json(
        audit_path,
        {
            "schema": "v194-identity-audit",
            "source": str(source),
            "output": str(output),
            "source_sha256": sha256(source),
            "output_sha256": sha256(output),
            "runtime": bpy.app.version_string,
            "created": sorted({obj.name for obj in created}),
            "hidden_predecessors": [BODY_NAME, HAIR_NAME],
            "protected_before": protected_before,
            "protected_after": protected_after,
            "protected_identical": protected_before == protected_after,
            "below_neck": below_neck,
            "landmarks": landmarks,
            "renders": render_manifest,
            "delivery": {"status": "pending host-Python contact-sheet composition"},
            "known_limits": [
                "Identity geometry is animation-oriented stylized construction, not photogrammetric likeness.",
                "Final pore, cloth, and travelling-contour treatment is reserved for V199 look development.",
            ],
        },
    )
    write_json(production / "renders" / "v194_render_manifest.json", {"schema": "v194-render-manifest-v1", "renders": render_manifest})
    status = production / "HEADLESS_BUILD_STATUS_V194.md"
    status.write_text(
        "# Character Asset_An — V194 Identity\n\n"
        "V194 replaces the juvenile blockout head with an adult, reference-aligned head/neck assembly, small ears, defined nose and jaw, tired off-axis gaze, closed mouth, close beard, split mustache, low brow dot, and dense short curls with one anatomical-left part.\n\n"
        f"- Source SHA-256: `{sha256(source)}`\n"
        f"- Output SHA-256: `{sha256(output)}`\n"
        f"- Protected fingerprint: `{protected_before['sha256']}` before and after\n"
        f"- Below-neck vertices: `{below_neck['count']}` unchanged\n"
        "- Structural and reopen validation: run after visual gate\n"
        "- Primary contact: `delivery/v194_identity_six_view_contact.png` (composed after Blender exits)\n"
        "- Baseline comparison: `delivery/v193_to_v194_identity_comparison.png` (composed after Blender exits)\n",
        encoding="utf-8",
    )
    print("V194_OUTPUT=" + str(output))
    print("V194_AUDIT=" + str(audit_path))


if __name__ == "__main__":
    main()
