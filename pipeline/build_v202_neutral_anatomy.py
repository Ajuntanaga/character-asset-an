from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.common import sha256, write_json
from pipeline.photoreal_contract import PHOTOREAL_CONTRACT


STAGE = ROOT / "production_v202_neutral_anatomy"
SOURCE = ROOT / "production_v201_reference_lock" / "ant_photoreal_reference_v201.blend"
OUTPUT = STAGE / "ant_neutral_anatomy_v202.blend"
BUILDING = STAGE / ".ant_neutral_anatomy_v202.building.blend"
EXPECTED_SOURCE_SHA256 = "56e56c3e996162cccf64c27f3c7bb5916e823caaf6915f6e8a52ae949dffa6dc"
EXPECTED_V200_SHA256 = "42612cfbd1cbeed03c0db1eb085ea10f1ca73fe3697404ad563d1cb15599c6d1"
EXPECTED_V192_SHA256 = "443321b43df4ada529113854f935b393e2e523fbbd36beb08c53fb0d08048148"

# These points are only search seeds recovered from the accepted interactive
# surface probe.  The builder ray-casts the current evaluated body and the
# validator independently repeats that live-surface test; it never accepts a
# nail merely because a stored coordinate matches this list.
TOE_RAYCAST_SEEDS_L = [
    (0.2260, -0.0910, 0.0270),
    (0.2380, -0.0940, 0.0276),
    (0.2500, -0.0970, 0.0245),
    (0.2630, -0.0770, 0.0245),
    (0.2760, -0.0630, 0.0250),
]

RENDER_VIEWS = {
    "body_front": ("V202_CAM_BODY_FRONT", (1200, 1600)),
    "body_profile": ("V202_CAM_BODY_PROFILE", (1200, 1600)),
    "body_back": ("V202_CAM_BODY_BACK", (1200, 1600)),
    "body_three_quarter_l": ("V202_CAM_BODY_THREE_QUARTER_L", (1200, 1600)),
    "body_three_quarter_r": ("V202_CAM_BODY_THREE_QUARTER_R", (1200, 1600)),
    "head_front": ("V202_CAM_HEAD_FRONT", (1600, 1600)),
    "head_profile": ("V202_CAM_HEAD_PROFILE", (1600, 1600)),
    "head_three_quarter": ("V202_CAM_HEAD_THREE_QUARTER", (1600, 1600)),
    "hands": ("V202_CAM_HANDS", (1600, 900)),
    "feet": ("V202_CAM_FEET", (1600, 900)),
    "hand_left": ("V202_CAM_HAND_L", (1200, 1600)),
    "hand_right": ("V202_CAM_HAND_R", (1200, 1600)),
    "foot_left": ("V202_CAM_FOOT_L", (1200, 1600)),
    "foot_right": ("V202_CAM_FOOT_R", (1200, 1600)),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def smoothstep(low: float, high: float, value: float) -> float:
    if high == low:
        return float(value >= high)
    t = max(0.0, min(1.0, (value - low) / (high - low)))
    return t * t * (3.0 - 2.0 * t)


def band(value: float, low: float, high: float, feather: float) -> float:
    return smoothstep(low - feather, low + feather, value) * (1.0 - smoothstep(high - feather, high + feather, value))


def material(
    name: str,
    color: tuple[float, float, float, float],
    roughness: float,
    metallic: float = 0.0,
) -> bpy.types.Material:
    value = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    value.use_nodes = True
    principled = value.node_tree.nodes.get("Principled BSDF")
    principled.inputs["Base Color"].default_value = color
    principled.inputs["Roughness"].default_value = roughness
    principled.inputs["Metallic"].default_value = metallic
    return value


def assign_material(obj: bpy.types.Object, value: bpy.types.Material) -> None:
    obj.data.materials.clear()
    obj.data.materials.append(value)


def relink(obj: bpy.types.Object, collection: bpy.types.Collection) -> None:
    for owner in list(obj.users_collection):
        owner.objects.unlink(obj)
    collection.objects.link(obj)


def activate(obj: bpy.types.Object) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def world_points(obj: bpy.types.Object) -> list[Vector]:
    return [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]


def bounds(obj: bpy.types.Object) -> tuple[Vector, Vector]:
    points = world_points(obj)
    return (
        Vector(tuple(min(point[index] for point in points) for index in range(3))),
        Vector(tuple(max(point[index] for point in points) for index in range(3))),
    )


def band_bounds(points: list[Vector], z0: float, z1: float, x_limit: float | None = None) -> dict[str, float]:
    selected = [point for point in points if z0 <= point.z <= z1 and (x_limit is None or abs(point.x) <= x_limit)]
    require(bool(selected), f"No landmarks for band z={z0}:{z1}")
    return {
        "width_m": max(point.x for point in selected) - min(point.x for point in selected),
        "depth_m": max(point.y for point in selected) - min(point.y for point in selected),
        "center_x_m": (max(point.x for point in selected) + min(point.x for point in selected)) / 2.0,
        "center_y_m": (max(point.y for point in selected) + min(point.y for point in selected)) / 2.0,
    }


def capture_measurements(body: bpy.types.Object) -> dict[str, object]:
    points = world_points(body)
    minimum, maximum = bounds(body)
    height = maximum.z - minimum.z
    return {
        "height_m": height,
        "overall_width_m": maximum.x - minimum.x,
        "overall_depth_m": maximum.y - minimum.y,
        "head": band_bounds(points, 1.56, 1.79999, 0.13),
        "midface": band_bounds(points, 1.62, 1.70, 0.13),
        "jaw": band_bounds(points, 1.56, 1.63, 0.13),
        # Measure the upper-neck silhouette directly.  The former broad band
        # used an abs(x) cutoff through the trapezius; inward deformation could
        # pull previously excluded vertices into that sample and paradoxically
        # report a wider neck.  This narrow uncapped slice is continuous and
        # stays above the shoulder/trapezius fan.
        "neck": band_bounds(points, 1.535, 1.555),
        "upper_torso": band_bounds(points, 1.25, 1.49, 0.36),
        "chest": band_bounds(points, 1.25, 1.48, 0.28),
        "waist": band_bounds(points, 1.02, 1.18, 0.22),
        "hips": band_bounds(points, 0.86, 1.03, 0.23),
        "thighs": band_bounds(points, 0.54, 0.87, 0.25),
    }


def apply_reference_match_delta(body: bpy.types.Object) -> dict[str, object]:
    """Apply the bounded supplied-reference correction once.

    This is a separate, idempotence-marked delta so the same deterministic
    operation can repair the currently open canonical V202 file and can also
    be called by a clean V201-to-V202 rebuild.
    """
    version = "v202-supplied-reference-match-v2"
    require(body.get("reference_match_correction") != version, f"Reference correction already applied: {version}")
    inverse = body.matrix_world.inverted()
    affected = {"head": 0, "jaw": 0, "neck": 0, "torso": 0, "lips": 0, "nose": 0}
    for vertex in body.data.vertices:
        point = body.matrix_world @ vertex.co
        x, y, z = point

        # Preserve cheek breadth while tapering the widest lower jaw/chin into
        # the compact oval seen in the supplied front and three-quarter views.
        head = smoothstep(1.535, 1.575, z)
        upper_cranium = smoothstep(1.695, 1.755, z)
        midface = band(z, 1.620, 1.705, 0.024) * (1.0 - smoothstep(0.100, 0.124, abs(x)))
        jaw = band(z, 1.545, 1.635, 0.025) * (1.0 - smoothstep(0.108, 0.128, abs(x)))
        chin = band(z, 1.540, 1.595, 0.018) * (1.0 - smoothstep(0.070, 0.095, abs(x)))
        x *= 1.0 - 0.018 * upper_cranium - 0.035 * midface - 0.105 * jaw - 0.060 * chin

        # Narrow the neck/trapezius and average-to-lean torso silhouette while
        # retaining the capable arms and the established A-pose landmarks.
        neck = band(z, 1.445, 1.585, 0.035) * (1.0 - smoothstep(0.125, 0.155, abs(x)))
        trapezius = band(z, 1.385, 1.555, 0.045) * smoothstep(0.075, 0.135, abs(x)) * (1.0 - smoothstep(0.285, 0.33, abs(x)))
        torso = band(z, 0.985, 1.455, 0.075) * (1.0 - smoothstep(0.235, 0.285, abs(x)))
        shoulder = band(z, 1.205, 1.505, 0.080) * smoothstep(0.190, 0.245, abs(x))
        thigh = band(z, 0.505, 0.965, 0.095) * (1.0 - smoothstep(0.220, 0.275, abs(x)))
        x *= 1.0 - 0.095 * neck - 0.050 * trapezius - 0.045 * torso - 0.050 * shoulder
        y *= 1.0 - 0.055 * neck - 0.075 * trapezius - 0.070 * torso - 0.065 * shoulder - 0.045 * thigh
        if thigh > 0.0:
            sign = -1.0 if x < 0.0 else 1.0
            center = 0.102 * sign
            x = center + (x - center) * (1.0 - 0.040 * thigh)

        # Broaden and round the alar base independently of cheek width.  Add
        # upper/lower lip volume around the existing closed seam without
        # opening the mouth or moving the oral assets forward.
        front = smoothstep(-0.090, -0.116, y)
        nose = band(z, 1.622, 1.681, 0.016) * front * (1.0 - smoothstep(0.044, 0.058, abs(x)))
        alar = band(z, 1.625, 1.653, 0.010) * smoothstep(-0.106, -0.123, y) * smoothstep(0.006, 0.015, abs(x)) * (1.0 - smoothstep(0.030, 0.043, abs(x)))
        lips = band(z, 1.570, 1.618, 0.010) * smoothstep(-0.100, -0.119, y) * (1.0 - smoothstep(0.052, 0.066, abs(x)))
        x *= 1.0 + 0.055 * nose + 0.075 * alar + 0.025 * lips
        y -= 0.0020 * nose + 0.0025 * lips
        lip_center = 1.593
        z = lip_center + (z - lip_center) * (1.0 + 0.180 * lips)

        if head > 0.0:
            affected["head"] += 1
        if jaw > 0.0:
            affected["jaw"] += 1
        if neck > 0.0:
            affected["neck"] += 1
        if torso > 0.0 or shoulder > 0.0 or thigh > 0.0:
            affected["torso"] += 1
        if lips > 0.0:
            affected["lips"] += 1
        if nose > 0.0:
            affected["nose"] += 1
        vertex.co = inverse @ Vector((x, y, z))

    body.data.update()
    body["reference_match_correction"] = version
    body["reference_match_authority"] = "supplied face sheet and turnaround; generated photoreal face is lower-authority guidance"
    body["reference_match_affected_vertices"] = json.dumps(affected, sort_keys=True)
    return {"version": version, "affected_vertices": affected}


def reshape_body(body: bpy.types.Object) -> tuple[dict[str, object], dict[str, object]]:
    before = capture_measurements(body)
    inverse = body.matrix_world.inverted()
    for vertex in body.data.vertices:
        point = body.matrix_world @ vertex.co
        x, y, z = point

        # Soften the scan's bodybuilder mass without changing the A-pose.  The
        # final height normalization below restores the exact 1.80 m lock.
        torso = band(z, 1.02, 1.49, 0.08) * (1.0 - smoothstep(0.23, 0.30, abs(x)))
        chest = band(z, 1.24, 1.47, 0.07) * (1.0 - smoothstep(0.20, 0.29, abs(x)))
        shoulders_arms = band(z, 1.08, 1.50, 0.10) * smoothstep(0.20, 0.27, abs(x))
        thigh = band(z, 0.53, 0.96, 0.10) * (1.0 - smoothstep(0.22, 0.28, abs(x)))
        glute = band(z, 0.82, 1.07, 0.08) * (1.0 - smoothstep(0.22, 0.28, abs(x))) * smoothstep(0.025, 0.085, y)

        x *= 1.0 - 0.032 * torso - 0.018 * chest - 0.018 * shoulders_arms
        y *= 1.0 - 0.065 * torso - 0.085 * chest - 0.090 * shoulders_arms - 0.075 * glute
        if thigh > 0.0:
            sign = -1.0 if x < 0.0 else 1.0
            center = 0.102 * sign
            x = center + (x - center) * (1.0 - 0.080 * thigh)
            y *= 1.0 - 0.075 * thigh

        # Identity shaping: broader compact midface/jaw, wider natural nose,
        # fuller closed lips, and a firmer brow plane. All fields are smooth and
        # preserve the source topology and multires displacement structure.
        head = smoothstep(1.535, 1.575, z)
        upper_cranium = smoothstep(1.695, 1.755, z)
        midface = band(z, 1.615, 1.705, 0.025) * (1.0 - smoothstep(0.105, 0.125, abs(x)))
        jaw = band(z, 1.555, 1.635, 0.025) * (1.0 - smoothstep(0.105, 0.125, abs(x)))
        chin = band(z, 1.545, 1.595, 0.018) * (1.0 - smoothstep(0.060, 0.085, abs(x)))
        front_face = smoothstep(-0.070, -0.105, y)
        nose = band(z, 1.625, 1.685, 0.018) * smoothstep(-0.090, -0.120, y) * (1.0 - smoothstep(0.038, 0.055, abs(x)))
        lips = band(z, 1.575, 1.615, 0.012) * smoothstep(-0.102, -0.122, y) * (1.0 - smoothstep(0.048, 0.064, abs(x)))
        brow = band(z, 1.685, 1.725, 0.012) * front_face * (1.0 - smoothstep(0.083, 0.105, abs(x)))

        # Adult compact oval-rectangular identity: reduce the high round dome,
        # carry width through the cheek/jaw, project brow/nose/lips, and retain
        # a credible chin rather than a childlike tapered lower face.
        x *= 1.0 - 0.145 * upper_cranium + 0.095 * midface + 0.125 * jaw + 0.060 * nose + 0.090 * chin + 0.045 * lips
        y *= 1.0 - 0.025 * head
        y -= 0.0060 * brow + 0.0045 * nose + 0.0040 * lips + 0.0030 * chin
        z -= 0.0030 * midface + 0.0080 * jaw + 0.0100 * chin
        if z > 1.695:
            z = 1.695 + (z - 1.695) * (1.0 - 0.265 * upper_cranium)

        vertex.co = inverse @ Vector((x, y, z))

    body.data.update()
    apply_reference_match_delta(body)
    # Preserve the exact barefoot-height contract after compacting the skull.
    minimum, maximum = bounds(body)
    height_scale = 1.80 / (maximum.z - minimum.z)
    for vertex in body.data.vertices:
        point = body.matrix_world @ vertex.co
        point.z = (point.z - minimum.z) * height_scale
        vertex.co = inverse @ point
    body.data.update()
    body["v202_height_normalization_scale"] = float(height_scale)
    multires = next((modifier for modifier in body.modifiers if modifier.type == "MULTIRES"), None)
    require(multires is not None and multires.total_levels >= 3, "Source multires detail missing")
    multires.levels = min(2, multires.total_levels)
    multires.sculpt_levels = min(2, multires.total_levels)
    multires.render_levels = min(2, multires.total_levels)
    after = capture_measurements(body)
    return before, after


def add_uv_ellipsoid(
    name: str,
    collection: bpy.types.Collection,
    location: tuple[float, float, float],
    scale: tuple[float, float, float],
    value: bpy.types.Material,
    rotation: tuple[float, float, float] = (0.0, 0.0, 0.0),
    segments: int = 24,
    rings: int = 12,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.data.name = name + "_MESH"
    relink(obj, collection)
    obj.scale = scale
    activate(obj)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign_material(obj, value)
    bpy.ops.object.shade_smooth()
    return obj


def add_nail_bed_plate(
    name: str,
    collection: bpy.types.Collection,
    body_bvh: BVHTree,
    surface_point: Vector,
    surface_normal: Vector,
    digit_forward: Vector,
    width: float,
    length: float,
    thickness: float,
    value: bpy.types.Material,
    digit_index: int,
    side_name: str,
) -> bpy.types.Object:
    """Create one connected plate conformed across the evaluated nail bed."""
    normal = surface_normal.normalized()
    tangent_forward = (digit_forward - normal * digit_forward.dot(normal)).normalized()
    tangent_side = tangent_forward.cross(normal).normalized()
    segments = 24
    rings = 4
    half_width = width / 2.0
    half_length = length / 2.0
    surface_offset = 0.00024
    center_nearest = body_bvh.find_nearest(surface_point, 0.010)
    require(center_nearest is not None, f"No body surface for nail center: {name}")
    center_hit, center_normal, _face_index, _distance = center_nearest
    vertices: list[tuple[float, float, float]] = [tuple(center_hit + center_normal.normalized() * surface_offset)]
    sampled_surface: list[list[float]] = [list(center_hit)]
    for ring in range(1, rings + 1):
        radius = ring / rings
        for index in range(segments):
            angle = 2.0 * math.pi * index / segments
            cosine, sine = math.cos(angle), math.sin(angle)
            # A mildly squared superellipse follows a real nail-bed outline.
            x = half_width * radius * math.copysign(abs(cosine) ** 0.70, cosine)
            y = half_length * radius * math.copysign(abs(sine) ** 0.70, sine)
            query = surface_point + tangent_side * x + tangent_forward * y
            # Cast along the center nail-bed normal. A nearest-point query can
            # jump across the interdigital gap onto an adjacent toe/sidewall,
            # folding one connected shell into visible lobes.
            hit, hit_normal, _face_index, _distance = body_bvh.ray_cast(
                query + normal * 0.008,
                -normal,
                0.016,
            )
            if hit is None or hit_normal is None or hit_normal.normalized().dot(normal) < 0.35:
                # The reduced dimensions keep this fallback inside the nail
                # bed; it preserves a smooth tangent shell at a silhouette edge.
                hit = center_hit + tangent_side * x + tangent_forward * y
                hit_normal = center_normal
            vertices.append(tuple(hit + hit_normal.normalized() * surface_offset))
            sampled_surface.append(list(hit))
    faces: list[tuple[int, ...]] = []
    for index in range(segments):
        nxt = (index + 1) % segments
        faces.append((0, 1 + index, 1 + nxt))
    for ring in range(1, rings):
        inner = 1 + (ring - 1) * segments
        outer = 1 + ring * segments
        for index in range(segments):
            nxt = (index + 1) % segments
            faces.append((inner + index, outer + index, outer + nxt, inner + nxt))

    mesh = bpy.data.meshes.new(name + "_MESH")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    assign_material(obj, value)
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    solidify = obj.modifiers.new("V202_NAIL_PLATE_THICKNESS", "SOLIDIFY")
    solidify.thickness = thickness
    solidify.offset = -1.0
    solidify.use_rim = True
    obj["geometry_class"] = "single_shell_surface_conformed_nail_plate"
    obj["digit_index"] = digit_index
    obj["anatomical_side"] = side_name
    obj["plate_width_m"] = width
    obj["plate_length_m"] = length
    obj["plate_thickness_m"] = thickness
    obj["surface_point_m"] = list(center_hit)
    obj["surface_normal"] = list(center_normal.normalized())
    obj["surface_offset_m"] = surface_offset
    obj["surface_sample_count"] = len(sampled_surface)
    obj["landmark_method"] = "multi-sample evaluated V202_BODY nail-bed conformance from regression seed"
    return obj


def rebuild_toenails(
    body: bpy.types.Object,
    anatomy: bpy.types.Collection,
    nail_material: bpy.types.Material,
) -> list[bpy.types.Object]:
    """Rebuild all ten toe plates from the current evaluated body surface."""
    for obj in list(anatomy.all_objects):
        if obj.name.startswith("V202_NAIL_FOOT_"):
            bpy.data.objects.remove(obj, do_unlink=True)

    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = body.evaluated_get(depsgraph)
    evaluated_mesh = evaluated.to_mesh()
    world = evaluated.matrix_world
    points = [world @ vertex.co for vertex in evaluated_mesh.vertices]
    polygons = [tuple(polygon.vertices) for polygon in evaluated_mesh.polygons]
    bvh = BVHTree.FromPolygons(points, polygons, all_triangles=False)
    created: list[bpy.types.Object] = []
    dimensions = [
        (0.0090, 0.0112, 0.00012),
        (0.0064, 0.0080, 0.00011),
        (0.0059, 0.0074, 0.00011),
        (0.0054, 0.0068, 0.00010),
        (0.0049, 0.0062, 0.00010),
    ]
    try:
        for side_name, sign in (("L", 1.0), ("R", -1.0)):
            prior_hits: list[Vector] = []
            for digit_index, (seed_raw, plate_dims) in enumerate(zip(TOE_RAYCAST_SEEDS_L, dimensions), 1):
                seed = Vector((seed_raw[0] * sign, seed_raw[1], seed_raw[2]))
                origin = Vector((seed.x, seed.y, seed.z + 0.040))
                hit, normal, _face_index, _distance = bvh.ray_cast(origin, Vector((0.0, 0.0, -1.0)), 0.10)
                if hit is None or normal is None:
                    nearest = bvh.find_nearest(seed, 0.020)
                    require(nearest is not None, f"No evaluated toe surface near seed {tuple(seed)}")
                    hit, normal, _face_index, _distance = nearest
                require((hit - seed).length <= 0.012, f"Toe raycast left regression region: side={side_name} digit={digit_index} delta={(hit - seed).length}")
                require(all((hit - prior).length >= 0.006 for prior in prior_hits), f"Toe raycasts collapsed onto one digit: side={side_name} digit={digit_index}")
                prior_hits.append(hit.copy())
                width, length, thickness = plate_dims
                obj = add_nail_bed_plate(
                    f"V202_NAIL_FOOT_{side_name}_{digit_index:02d}",
                    anatomy,
                    bvh,
                    hit,
                    normal,
                    Vector((0.0, -1.0, 0.0)),
                    width,
                    length,
                    thickness,
                    nail_material,
                    digit_index,
                    side_name,
                )
                obj["seed_regression_delta_m"] = float((hit - seed).length)
                created.append(obj)
    finally:
        evaluated.to_mesh_clear()
    return created


def add_cylinder(
    name: str,
    collection: bpy.types.Collection,
    location: tuple[float, float, float],
    radius: float,
    depth: float,
    value: bpy.types.Material,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=radius, depth=depth, location=location, rotation=(math.pi / 2.0, 0.0, 0.0))
    obj = bpy.context.object
    obj.name = name
    obj.data.name = name + "_MESH"
    relink(obj, collection)
    assign_material(obj, value)
    bevel = obj.modifiers.new("V202_EDGE_SOFTEN", "BEVEL")
    bevel.width = 0.0004
    bevel.segments = 2
    return obj


def add_sclera_fitted_cap(
    name: str,
    collection: bpy.types.Collection,
    sclera_minimum: Vector,
    sclera_maximum: Vector,
    visual_center_z_offset: float,
    radius: float,
    forward_offset: float,
    value: bpy.types.Material,
    role: str,
) -> bpy.types.Object:
    """Build a curved iris/pupil cap directly on the live scleral ellipsoid."""
    center = (sclera_minimum + sclera_maximum) / 2.0
    radii = (sclera_maximum - sclera_minimum) / 2.0
    visual_z = center.z + visual_center_z_offset
    segments, rings = 32, 6
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []

    def surface_y(x: float, z: float) -> float:
        normalized = ((x - center.x) / radii.x) ** 2 + ((z - center.z) / radii.z) ** 2
        require(normalized < 1.0, f"{name} exceeds live sclera bounds")
        return center.y - radii.y * math.sqrt(1.0 - normalized) - forward_offset

    vertices.append((center.x, surface_y(center.x, visual_z), visual_z))
    for ring in range(1, rings + 1):
        ring_radius = radius * ring / rings
        for segment in range(segments):
            angle = 2.0 * math.pi * segment / segments
            x = center.x + math.cos(angle) * ring_radius
            z = visual_z + math.sin(angle) * ring_radius
            vertices.append((x, surface_y(x, z), z))
    for segment in range(segments):
        faces.append((0, 1 + segment, 1 + (segment + 1) % segments))
    for ring in range(1, rings):
        inner = 1 + (ring - 1) * segments
        outer = 1 + ring * segments
        for segment in range(segments):
            next_segment = (segment + 1) % segments
            faces.append((inner + segment, outer + segment, outer + next_segment, inner + next_segment))

    mesh = bpy.data.meshes.new(name + "_MESH")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    assign_material(obj, value)
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    obj["anatomy_role"] = role
    obj["fitted_sclera"] = "_".join(name.split("_")[:3]) + "_SCLERA"
    obj["cap_radius_m"] = radius
    obj["forward_offset_m"] = forward_offset
    obj["visual_center_z_offset_m"] = visual_center_z_offset
    obj["visual_center_world_m"] = [center.x, surface_y(center.x, visual_z), visual_z]
    obj["curved_cap"] = True
    return obj


def add_arc(
    name: str,
    collection: bpy.types.Collection,
    center: tuple[float, float, float],
    radius_x: float,
    radius_z: float,
    start: float,
    end: float,
    value: bpy.types.Material,
    bevel_depth: float = 0.00014,
) -> bpy.types.Object:
    curve = bpy.data.curves.new(name + "_CURVE", "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 2
    curve.bevel_depth = bevel_depth
    curve.bevel_resolution = 2
    spline = curve.splines.new("POLY")
    count = 25
    spline.points.add(count - 1)
    cx, cy, cz = center
    for index, point in enumerate(spline.points):
        angle = start + (end - start) * index / (count - 1)
        point.co = (cx + math.cos(angle) * radius_x, cy, cz + math.sin(angle) * radius_z, 1.0)
    obj = bpy.data.objects.new(name, curve)
    collection.objects.link(obj)
    assign_material(obj, value)
    activate(obj)
    bpy.ops.object.convert(target="MESH")
    obj.data.name = name + "_MESH"
    return obj


def create_anatomy(body: bpy.types.Object, old_collection: bpy.types.Collection) -> tuple[bpy.types.Collection, dict[str, list[float]]]:
    anatomy = bpy.data.collections.new("V202_ANATOMY")
    bpy.context.scene.collection.children.link(anatomy)
    clay = material("MAT_V202_NEUTRAL_CLAY", (0.32, 0.17, 0.105, 1.0), 0.58)
    sclera_mat = material("MAT_V202_SCLERA_CLAY", (0.26, 0.225, 0.19, 1.0), 0.46)
    iris_mat = material("MAT_V202_IRIS_BROWN", (0.020, 0.009, 0.004, 1.0), 0.38)
    cornea_mat = material("MAT_V202_CORNEA", (0.12, 0.11, 0.10, 1.0), 0.12)
    wet_mat = material("MAT_V202_WET_ANATOMY", (0.105, 0.025, 0.018, 1.0), 0.34)
    oral_mat = material("MAT_V202_ORAL_DARK", (0.055, 0.010, 0.008, 1.0), 0.46)
    gum_mat = material("MAT_V202_GUM", (0.25, 0.045, 0.038, 1.0), 0.42)
    tooth_mat = material("MAT_V202_TOOTH", (0.66, 0.58, 0.45, 1.0), 0.34)
    tongue_mat = material("MAT_V202_TONGUE", (0.31, 0.055, 0.045, 1.0), 0.40)
    nail_mat = material("MAT_V202_NAIL_PLATE", (0.42, 0.21, 0.15, 1.0), 0.38)
    for eye_material in (iris_mat, oral_mat, wet_mat):
        principled = eye_material.node_tree.nodes.get("Principled BSDF")
        if principled and "Specular IOR Level" in principled.inputs:
            principled.inputs["Specular IOR Level"].default_value = 0.18
    assign_material(body, clay)
    height_scale = float(body.get("v202_height_normalization_scale", 1.0))

    def zc(value: float) -> float:
        return value * height_scale

    centers: dict[str, list[float]] = {}
    eye_centers: dict[str, Vector] = {}
    for side in ("L", "R"):
        source_eye = bpy.data.objects.get(f"V201_BASE_EYE_{side}")
        require(source_eye is not None and source_eye.type == "MESH", f"Missing V201 eye {side}")
        source_eye.name = f"V202_EYE_{side}_SCLERA"
        source_eye.data.name = source_eye.name + "_MESH"
        eye_inverse = source_eye.matrix_world.inverted()
        for vertex in source_eye.data.vertices:
            eye_point = source_eye.matrix_world @ vertex.co
            eye_point.z = zc(eye_point.z)
            vertex.co = eye_inverse @ eye_point
        source_eye.data.update()
        source_eye.location.x *= 1.04
        # The cap fit must use the shifted live eye transform.  Blender can
        # leave matrix_world stale until the view layer updates, which would
        # offset iris/pupil gaze from the reopened sclera by about 1.4 mm.
        bpy.context.view_layer.update()
        relink(source_eye, anatomy)
        assign_material(source_eye, sclera_mat)
        # Use current vertices, not Object.bound_box: the latter can remain
        # stale immediately after the height-normalization edit.
        eye_points = world_points(source_eye)
        eye_minimum = Vector(tuple(min(point[index] for point in eye_points) for index in range(3)))
        eye_maximum = Vector(tuple(max(point[index] for point in eye_points) for index in range(3)))
        center = (eye_minimum + eye_maximum) / 2.0
        eye_centers[side] = center

        cornea = source_eye.copy()
        cornea.data = source_eye.data.copy()
        cornea.name = f"V202_EYE_{side}_CORNEA"
        cornea.data.name = cornea.name + "_MESH"
        anatomy.objects.link(cornea)
        cornea.scale = (1.025, 1.025, 1.025)
        assign_material(cornea, cornea_mat)
        # Geometry is retained for the production eye contract, but the clay
        # gate does not render a duplicate full-eye shell.
        cornea.hide_render = True
        cornea["anatomy_role"] = "corneal_shell"

        iris = add_sclera_fitted_cap(
            f"V202_EYE_{side}_IRIS",
            anatomy,
            eye_minimum,
            eye_maximum,
            -0.0015,
            0.0058,
            0.00006,
            iris_mat,
            "curved_iris_cap",
        )
        pupil = add_sclera_fitted_cap(
            f"V202_EYE_{side}_PUPIL",
            anatomy,
            eye_minimum,
            eye_maximum,
            -0.0015,
            0.00215,
            0.00014,
            oral_mat,
            "curved_pupil_cap",
        )
        lid_y = eye_minimum.y - 0.00005
        upper = add_arc(f"V202_LID_{side}_UPPER", anatomy, (center.x, lid_y, center.z), 0.0140, 0.0061, 0.0, math.pi, clay, 0.00013)
        lower = add_arc(f"V202_LID_{side}_LOWER", anatomy, (center.x, lid_y + 0.00018, center.z), 0.0140, 0.0046, math.pi, 2.0 * math.pi, clay, 0.00011)
        for lid in (upper, lower):
            lid["anatomy_role"] = "subtle_lid_margin"
            lid["display_subtle"] = True
            lid.hide_render = True
        inner_x = center.x - math.copysign(0.0145, center.x)
        tear = add_uv_ellipsoid(
            f"V202_TEAR_DUCT_{side}",
            anatomy,
            (inner_x, lid_y + 0.00025, center.z - 0.0010),
            (0.00115, 0.00042, 0.00072),
            wet_mat,
            segments=20,
            rings=10,
        )
        tear["anatomy_role"] = "contained_lacrimal_caruncle"
        tear["display_subtle"] = True
        tear.hide_render = True

    # Closed-lip internal anatomy; these assets sit posterior to the exterior lip surface.
    add_uv_ellipsoid("V202_ORAL_CAVITY", anatomy, (0.0, -0.080, zc(1.594)), (0.037, 0.014, 0.018), oral_mat)
    add_uv_ellipsoid("V202_GUM_UPPER", anatomy, (0.0, -0.091, zc(1.601)), (0.031, 0.006, 0.007), gum_mat)
    add_uv_ellipsoid("V202_GUM_LOWER", anatomy, (0.0, -0.089, zc(1.584)), (0.030, 0.006, 0.006), gum_mat)
    add_uv_ellipsoid("V202_TEETH_UPPER", anatomy, (0.0, -0.098, zc(1.598)), (0.028, 0.0045, 0.007), tooth_mat)
    add_uv_ellipsoid("V202_TEETH_LOWER", anatomy, (0.0, -0.097, zc(1.586)), (0.027, 0.0045, 0.006), tooth_mat)
    add_uv_ellipsoid("V202_TONGUE", anatomy, (0.0, -0.078, zc(1.578)), (0.029, 0.013, 0.006), tongue_mat)
    for side, sign in (("L", 1.0), ("R", -1.0)):
        nostril = add_uv_ellipsoid(
            f"V202_NOSTRIL_DEPTH_{side}",
            anatomy,
            (0.0118 * sign, -0.1240, zc(1.637)),
            (0.0030, 0.0011, 0.00155),
            oral_mat,
            rotation=(0.0, 0.0, 0.10 * sign),
            segments=20,
            rings=10,
        )
        nostril["anatomy_role"] = "internal_nostril_depth"
        nostril["internal_depth_m"] = 0.003
    for side, sign in (("L", 1.0), ("R", -1.0)):
        ear_canal = add_uv_ellipsoid(
            f"V202_EAR_CANAL_{side}",
            anatomy,
            (0.0895 * sign, 0.004, zc(1.653)),
            (0.0015, 0.0030, 0.0038),
            oral_mat,
            segments=20,
            rings=10,
        )
        ear_canal["anatomy_role"] = "technical_internal_ear_depth"
        ear_canal.hide_render = True
        ear_canal.hide_viewport = True

    # Surface-snap nail plates to evaluated multires geometry.  The old base-
    # cage nearest-point query mapped four small toes to one coarse vertex.
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = body.evaluated_get(depsgraph)
    evaluated_mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in evaluated_mesh.vertices]
    tree = KDTree(len(points))
    for index, point in enumerate(points):
        tree.insert(point, index)
    tree.balance()

    def distinct_surface_points(targets: list[Vector], minimum_separation: float) -> list[tuple[Vector, float]]:
        selected: list[Vector] = []
        result: list[tuple[Vector, float]] = []
        for query in targets:
            candidates = tree.find_n(query, 128)
            choice = next(
                ((co, distance) for co, _index, distance in candidates if all((co - prior).length >= minimum_separation for prior in selected)),
                None,
            )
            require(choice is not None, f"No separated surface point near {tuple(query)}")
            selected.append(choice[0].copy())
            result.append((choice[0].copy(), float(choice[1])))
        return result

    hand_targets = [
        (0.405, -0.030, 0.928),
        (0.444, -0.020, 0.898),
        (0.464, -0.018, 0.870),
        (0.458, -0.015, 0.842),
        (0.438, -0.010, 0.824),
    ]
    for side_name, sign in (("L", 1.0), ("R", -1.0)):
        queries = [Vector((target[0] * sign, target[1], zc(target[2]))) for target in hand_targets]
        for index, (nearest, distance) in enumerate(distinct_surface_points(queries, 0.0050), 1):
            location = Vector((nearest.x, nearest.y - 0.0013, nearest.z))
            obj = add_uv_ellipsoid(
                f"V202_NAIL_HAND_{side_name}_{index:02d}",
                anatomy,
                tuple(location),
                (0.0040 if index > 1 else 0.0048, 0.00105, 0.0065 if index > 1 else 0.0060),
                nail_mat,
                rotation=(0.0, math.radians(-24.0 * sign), 0.0),
                segments=20,
                rings=10,
            )
            obj["surface_snap_distance_m"] = distance

    evaluated.to_mesh_clear()
    rebuild_toenails(body, anatomy, nail_mat)

    for obj in anatomy.all_objects:
        if obj.type == "MESH":
            center = sum((obj.matrix_world @ Vector(corner) for corner in obj.bound_box), Vector()) / 8.0
            centers[obj.name] = [round(value, 6) for value in center]
            obj["stage"] = "V202"
            obj["production_anatomy"] = True
    anatomy["purpose"] = "paired eyes/lids/tear anatomy, oral cavity, nostril/ear depth, and surface-fitted nail plates"
    anatomy["object_count"] = len(anatomy.all_objects)
    return anatomy, centers


def look_at(obj: bpy.types.Object, target: Vector) -> None:
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def add_camera(name: str, location: tuple[float, float, float], target: tuple[float, float, float], ortho_scale: float) -> bpy.types.Object:
    data = bpy.data.cameras.new(name + "_DATA")
    data.type = "ORTHO"
    data.ortho_scale = ortho_scale
    data.lens = 70.0
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = location
    look_at(obj, Vector(target))
    obj["stage"] = "V202"
    return obj


def add_area(name: str, location: tuple[float, float, float], energy: float, size: float, target: tuple[float, float, float]) -> bpy.types.Object:
    data = bpy.data.lights.new(name + "_DATA", "AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = location
    look_at(obj, Vector(target))
    return obj


def configure_scene(body: bpy.types.Object) -> dict[str, bpy.types.Object]:
    scene = bpy.context.scene
    scene.name = "V202_NEUTRAL_ANATOMY_SCENE"
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 12
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = 0.075
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 4
    scene.cycles.diffuse_bounces = 2
    scene.cycles.glossy_bounces = 2
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.image_settings.color_depth = "8"
    scene.render.film_transparent = False
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.world = scene.world or bpy.data.worlds.new("V202_STUDIO_WORLD")
    scene.world.color = (0.014, 0.018, 0.023)
    bpy.context.view_layer.material_override = None

    for obj in list(bpy.data.objects):
        if obj.type in {"CAMERA", "LIGHT"} or obj.name == "V201_INSPECTION_FLOOR":
            bpy.data.objects.remove(obj, do_unlink=True)

    bpy.ops.mesh.primitive_plane_add(size=8.0, location=(0.0, 0.0, -0.003))
    floor = bpy.context.object
    floor.name = "V202_STUDIO_FLOOR"
    assign_material(floor, material("MAT_V202_FLOOR", (0.030, 0.038, 0.047, 1.0), 0.72))

    cameras = {
        "V202_CAM_BODY_FRONT": add_camera("V202_CAM_BODY_FRONT", (0.0, -4.0, 0.92), (0.0, 0.0, 0.92), 1.96),
        "V202_CAM_BODY_PROFILE": add_camera("V202_CAM_BODY_PROFILE", (4.0, 0.0, 0.92), (0.0, 0.0, 0.92), 1.96),
        "V202_CAM_BODY_BACK": add_camera("V202_CAM_BODY_BACK", (0.0, 4.0, 0.92), (0.0, 0.0, 0.92), 1.96),
        "V202_CAM_BODY_THREE_QUARTER_L": add_camera("V202_CAM_BODY_THREE_QUARTER_L", (3.0, -3.0, 0.96), (0.0, 0.0, 0.92), 1.96),
        "V202_CAM_BODY_THREE_QUARTER_R": add_camera("V202_CAM_BODY_THREE_QUARTER_R", (-3.0, -3.0, 0.96), (0.0, 0.0, 0.92), 1.96),
        "V202_CAM_HEAD_FRONT": add_camera("V202_CAM_HEAD_FRONT", (0.0, -2.2, 1.685), (0.0, -0.01, 1.685), 0.31),
        "V202_CAM_HEAD_PROFILE": add_camera("V202_CAM_HEAD_PROFILE", (2.2, 0.0, 1.685), (0.0, -0.01, 1.685), 0.31),
        "V202_CAM_HEAD_THREE_QUARTER": add_camera("V202_CAM_HEAD_THREE_QUARTER", (1.7, -1.7, 1.695), (0.0, -0.01, 1.685), 0.31),
        "V202_CAM_HANDS": add_camera("V202_CAM_HANDS", (0.0, -3.0, 0.88), (0.0, 0.0, 0.88), 1.10),
        "V202_CAM_FEET": add_camera("V202_CAM_FEET", (0.0, -1.8, 0.62), (0.0, -0.035, 0.045), 0.58),
        "V202_CAM_HAND_L": add_camera("V202_CAM_HAND_L", (0.44, -2.2, 0.885), (0.44, 0.0, 0.885), 0.32),
        "V202_CAM_HAND_R": add_camera("V202_CAM_HAND_R", (-0.44, -2.2, 0.885), (-0.44, 0.0, 0.885), 0.32),
        "V202_CAM_FOOT_L": add_camera("V202_CAM_FOOT_L", (0.20, -1.25, 0.54), (0.20, -0.035, 0.045), 0.32),
        "V202_CAM_FOOT_R": add_camera("V202_CAM_FOOT_R", (-0.20, -1.25, 0.54), (-0.20, -0.035, 0.045), 0.32),
        "V202_CAM_TOPOLOGY_FRONT": add_camera("V202_CAM_TOPOLOGY_FRONT", (0.0, -4.0, 0.92), (0.0, 0.0, 0.92), 1.96),
    }
    add_area("V202_KEY", (2.7, -3.6, 4.2), 830.0, 3.2, (0.0, 0.0, 1.0))
    add_area("V202_FILL", (-3.0, -1.8, 2.8), 470.0, 2.8, (0.0, 0.0, 1.0))
    add_area("V202_RIM", (1.6, 3.0, 3.5), 720.0, 2.4, (0.0, 0.0, 1.0))
    add_area("V202_FACE_FILL", (-0.8, -2.0, 1.75), 120.0, 1.0, (0.0, -0.02, 1.68))
    return cameras


def topology_material() -> bpy.types.Material:
    value = bpy.data.materials.new("MAT_V202_TOPOLOGY_WIRE")
    value.use_nodes = True
    nodes = value.node_tree.nodes
    links = value.node_tree.links
    principled = nodes.get("Principled BSDF")
    principled.inputs["Roughness"].default_value = 0.65
    wire = nodes.new("ShaderNodeWireframe")
    wire.use_pixel_size = True
    wire.inputs["Size"].default_value = 1.15
    mix = nodes.new("ShaderNodeMixRGB")
    mix.blend_type = "MIX"
    mix.inputs[1].default_value = (0.34, 0.31, 0.28, 1.0)
    mix.inputs[2].default_value = (0.008, 0.010, 0.012, 1.0)
    links.new(wire.outputs["Fac"], mix.inputs[0])
    links.new(mix.outputs[0], principled.inputs["Base Color"])
    return value


def render_suite(body: bpy.types.Object, cameras: dict[str, bpy.types.Object]) -> dict[str, dict[str, object]]:
    scene = bpy.context.scene
    clay_dir = STAGE / "renders" / "clay"
    wire_dir = STAGE / "renders" / "wireframe"
    clay_dir.mkdir(parents=True, exist_ok=True)
    wire_dir.mkdir(parents=True, exist_ok=True)
    results: dict[str, dict[str, object]] = {}
    for label, (camera_name, resolution) in RENDER_VIEWS.items():
        scene.camera = cameras[camera_name]
        scene.render.resolution_x, scene.render.resolution_y = resolution
        scene.render.resolution_percentage = 100
        path = clay_dir / f"{label}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        require(path.is_file(), f"Missing render: {path}")
        results[label] = {"path": str(path.relative_to(ROOT)), "sha256": sha256(path), "resolution": list(resolution), "engine": "CYCLES", "device": "CPU"}

    original_materials = [material_slot.material for material_slot in body.material_slots]
    anatomy = bpy.data.collections.get("V202_ANATOMY")
    anatomy_visibility = {obj.name: obj.hide_render for obj in anatomy.all_objects} if anatomy else {}
    if anatomy:
        for obj in anatomy.all_objects:
            obj.hide_render = True
    assign_material(body, topology_material())
    scene.camera = cameras["V202_CAM_TOPOLOGY_FRONT"]
    scene.render.resolution_x = 1200
    scene.render.resolution_y = 1600
    path = wire_dir / "topology_front.png"
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    require(path.is_file(), f"Missing topology render: {path}")
    results["topology_front"] = {"path": str(path.relative_to(ROOT)), "sha256": sha256(path), "resolution": [1200, 1600], "engine": "CYCLES", "device": "CPU"}
    body.data.materials.clear()
    for old_material in original_materials:
        if old_material is not None:
            body.data.materials.append(old_material)
    if anatomy:
        for obj in anatomy.all_objects:
            obj.hide_render = anatomy_visibility[obj.name]
    return results


def repair_relative_dependencies() -> list[str]:
    dependencies: list[str] = []
    for image in bpy.data.images:
        if image.source != "FILE" or not image.filepath:
            continue
        absolute = Path(bpy.path.abspath(image.filepath)).resolve()
        require(absolute.is_relative_to(ROOT) and absolute.is_file(), f"Invalid V201 image dependency: {absolute}")
        relative = os.path.relpath(absolute, OUTPUT.parent).replace(os.sep, "/")
        image.filepath = "//" + relative
        dependencies.append(str(absolute.relative_to(ROOT)))
    return sorted(set(dependencies))


def main() -> None:
    require(not OUTPUT.exists(), f"Refusing to overwrite immutable checkpoint: {OUTPUT}")
    require(SOURCE.is_file() and sha256(SOURCE) == EXPECTED_SOURCE_SHA256, "Accepted V201 source hash mismatch")
    require(tuple(bpy.app.version) >= (5, 2, 2), f"Blender 5.2.2+ required: {bpy.app.version_string}")
    require(Path(bpy.data.filepath).resolve() == SOURCE.resolve(), "Builder must be launched with the accepted V201 file")

    stage_dirs = [STAGE / "analysis", STAGE / "audit", STAGE / "delivery", STAGE / "renders" / "clay", STAGE / "renders" / "wireframe"]
    for directory in stage_dirs:
        directory.mkdir(parents=True, exist_ok=True)

    scene = bpy.context.scene
    body = bpy.data.objects.get("V201_BASE_BODY_REALISTIC_MALE")
    require(body is not None and body.type == "MESH", "Accepted V201 body missing")
    body.name = "V202_BODY"
    body.data.name = "V202_BODY_MESH"
    body["source_stage"] = "V201"
    body["source_sha256"] = EXPECTED_SOURCE_SHA256
    body["deformation_method"] = "smooth topology-space anatomical fields"
    body["identity_target"] = "approved illustrated character translated to plausible real anatomy"
    base_collection = bpy.data.collections.get("V201_BASE_OFFICIAL_REALISTIC_MALE")
    require(base_collection is not None, "V201 base collection missing")
    base_collection.name = "V202_PRODUCTION_BODY"

    before, after = reshape_body(body)
    head_group = body.vertex_groups.get("V202_HEAD") or body.vertex_groups.new(name="V202_HEAD")
    head_indices = [vertex.index for vertex in body.data.vertices if (body.matrix_world @ vertex.co).z >= 1.535]
    head_group.add(head_indices, 1.0, "REPLACE")
    head_guide = bpy.data.objects.new("V202_HEAD", None)
    base_collection.objects.link(head_guide)
    head_guide.empty_display_type = "SPHERE"
    head_guide.empty_display_size = 0.025
    head_guide.location = (0.0, -0.01, 1.67)
    head_guide.hide_render = True
    head_guide["role"] = "head landmark and V202_HEAD vertex-group guide; body/head remain one continuous surface"

    anatomy, organ_centers = create_anatomy(body, base_collection)
    reference_collection = bpy.data.collections.get("V201_REFERENCE_IMAGES")
    require(reference_collection is not None, "V201 reference collection missing")
    reference_collection.name = "V202_REFERENCE_GUIDES"
    reference_collection.hide_render = True
    reference_collection["authority"] = "supplied references outrank generated interpretation plates"

    cameras = configure_scene(body)
    dependencies = repair_relative_dependencies()

    scene["checkpoint"] = "V202_NEUTRAL_ANATOMY"
    scene["stage"] = "V202"
    scene["source_v201_path"] = str(SOURCE.relative_to(ROOT))
    scene["source_v201_sha256"] = EXPECTED_SOURCE_SHA256
    scene["character_height_m"] = 1.80
    scene["body_deformation_method"] = "smooth topology-space anatomical fields"
    scene["neutral_pose"] = "production A-pose"
    scene["neutral_mouth_closed"] = True
    scene["lip_seal_gap_m"] = 0.0008
    scene["identity_authority"] = "supplied design lock, refined turnaround, and face sheet; generated plates guidance only"
    scene["v200_geometry_imported"] = False
    scene["surface_claim"] = "neutral clay anatomy and identity gate; no final photoreal surfacing claim"

    measurements = {
        "schema": "v202-landmark-measurements-v1",
        "checkpoint": "V202_NEUTRAL_ANATOMY",
        "source_v201_sha256": EXPECTED_SOURCE_SHA256,
        "deformation_method": "smooth topology-space anatomical fields",
        "height_lock_m": 1.80,
        "before": before,
        "after": after,
        "proportion_deltas": {
            key: {
                metric: after[key][metric] - before[key][metric]
                for metric in ("width_m", "depth_m")
            }
            for key in ("head", "midface", "jaw", "neck", "upper_torso", "chest", "waist", "hips", "thighs")
        },
        "identity_fields": [
            "slim compact oval head with preserved cheek breadth and tapered jaw/chin",
            "broader rounded natural alar base",
            "fuller sealed upper and lower lips",
            "reinforced brow plane",
            "narrowed neck/trapezius and average-to-lean torso, shoulder, chest, and thigh mass",
        ],
        "organ_centers_m": organ_centers,
        "reference_authority": "supplied references authoritative; generated plates lower-authority interpretation",
    }
    measurement_path = STAGE / "analysis" / "v202_landmark_measurements.json"
    write_json(measurement_path, measurements)
    scene["landmark_measurements_path"] = str(measurement_path.relative_to(ROOT))
    scene["landmark_measurements_json"] = json.dumps(measurements["proportion_deltas"], sort_keys=True)

    render_results = render_suite(body, cameras)
    render_manifest = {
        "schema": "v202-render-manifest-v1",
        "status": "PASS",
        "checkpoint": "V202_NEUTRAL_ANATOMY",
        "renderer": "Cycles CPU",
        "color_management": "AgX - Medium High Contrast",
        "samples": scene.cycles.samples,
        "long_edge_px": 1600,
        "renders": render_results,
    }
    render_manifest_path = STAGE / "audit" / "v202_render_manifest.json"
    write_json(render_manifest_path, render_manifest)

    bpy.ops.wm.save_as_mainfile(filepath=str(BUILDING), compress=True)
    require(BUILDING.is_file(), "Building checkpoint was not saved")
    os.replace(BUILDING, OUTPUT)
    output_hash = sha256(OUTPUT)
    render_manifest["canonical_output"] = {
        "path": str(OUTPUT.relative_to(ROOT)),
        "sha256": output_hash,
    }
    write_json(render_manifest_path, render_manifest)

    immutable = {}
    for version, expected in (("V201", EXPECTED_SOURCE_SHA256), ("V200", EXPECTED_V200_SHA256), ("V192", EXPECTED_V192_SHA256)):
        path = SOURCE if version == "V201" else ROOT / PHOTOREAL_CONTRACT["immutable_sources"][version]["path"]
        require(path.is_file() and sha256(path) == expected, f"Immutable {version} changed")
        immutable[version] = {"path": str(path.relative_to(ROOT)), "sha256": sha256(path)}

    receipt = {
        "schema": "v202-build-receipt-v1",
        "status": "PASS",
        "checkpoint": "V202_NEUTRAL_ANATOMY",
        "blender_version": bpy.app.version_string,
        "source": immutable["V201"],
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": output_hash, "bytes": OUTPUT.stat().st_size},
        "immutable_sources": immutable,
        "body": {
            "vertices": len(body.data.vertices),
            "polygons": len(body.data.polygons),
            "uv_layers": len(body.data.uv_layers),
            "multires_total_levels": next(modifier.total_levels for modifier in body.modifiers if modifier.type == "MULTIRES"),
        },
        "anatomy_object_count": len(anatomy.all_objects),
        "camera_count": len(cameras),
        "dependency_count": len(dependencies),
        "dependencies": dependencies,
        "render_manifest": {"path": str(render_manifest_path.relative_to(ROOT)), "sha256": sha256(render_manifest_path)},
        "measurement_record": {"path": str(measurement_path.relative_to(ROOT)), "sha256": sha256(measurement_path)},
    }
    receipt_path = STAGE / "audit" / "v202_build_receipt.json"
    write_json(receipt_path, receipt)
    print(f"V202_BUILD_OK output={OUTPUT.relative_to(ROOT)} sha256={output_hash} renders={len(render_results)}")


if __name__ == "__main__":
    main()
