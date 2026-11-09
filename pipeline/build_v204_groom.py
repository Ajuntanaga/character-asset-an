from __future__ import annotations

import json
import math
import random
import sys
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.common import sha256, write_json


STAGE = ROOT / "production_v204_groom"
SOURCE = ROOT / "production_v203_skin_eyes" / "ant_skin_eyes_v203.blend"
OUTPUT = STAGE / "ant_groomed_character_v204.blend"
EXPECTED_SOURCE_SHA256 = "749774436e1edc9ab5fd17edcf9aea29e82bcdb6201a5ef594b31fc1513ee6f1"
EXPECTED_V200_SHA256 = "42612cfbd1cbeed03c0db1eb085ea10f1ca73fe3697404ad563d1cb15599c6d1"
EXPECTED_V192_SHA256 = "443321b43df4ada529113854f935b393e2e523fbbd36beb08c53fb0d08048148"

PART_X = 0.031
MUSTACHE_GAP = 0.012
ROOT_OFFSET = 0.00032
SEEDS = {
    "scalp_undercoat": 20400,
    "scalp_guides": 20401,
    "scalp_dense": 20402,
    "scalp_clump": 20403,
    "scalp_frizz": 20404,
    "scalp_flyaway": 20405,
    "beard_guides": 20411,
    "beard_children": 20412,
    "mustache_left": 20421,
    "mustache_right": 20422,
    "brows": 20431,
    "lashes": 20441,
}

RENDER_VIEWS = {
    "front": ("V204_CAM_FRONT", (640, 640), "neutral"),
    "profile": ("V204_CAM_PROFILE", (640, 640), "neutral"),
    "rear": ("V204_CAM_REAR", (640, 640), "rim"),
    "top": ("V204_CAM_TOP", (640, 640), "neutral"),
    "rim": ("V204_CAM_RIM", (640, 640), "rim"),
    "root_macro": ("V204_CAM_ROOT_MACRO", (768, 768), "macro"),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


class Surface:
    def __init__(self, obj: bpy.types.Object):
        self.obj = obj
        self.inverse = obj.matrix_world.inverted()
        self.normal_matrix = obj.matrix_world.to_3x3().inverted().transposed()
        self.bvh = BVHTree.FromObject(obj, bpy.context.evaluated_depsgraph_get())

    def nearest(self, point_world: Vector) -> tuple[Vector, Vector]:
        location, normal, _index, _distance = self.bvh.find_nearest(self.inverse @ point_world)
        require(location is not None and normal is not None, "Could not snap groom root to body")
        world_location = self.obj.matrix_world @ location
        world_normal = (self.normal_matrix @ normal).normalized()
        return world_location + world_normal * ROOT_OFFSET, world_normal


def hair_material(name: str, melanin: float, roughness: float, tint: tuple[float, float, float, float]) -> bpy.types.Material:
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    # Legacy curve bevels are tubular surfaces rather than Cycles hair
    # primitives.  Principled Surface therefore gives predictable eumelanin-
    # black fibers while retaining anisotropic longitudinal highlights.
    hair = nodes.new("ShaderNodeBsdfPrincipled")
    hair.name = f"{name}_FIBER_PRINCIPLED"
    hair.inputs["Base Color"].default_value = tint
    hair.inputs["Roughness"].default_value = roughness
    hair.inputs["IOR"].default_value = 1.55
    hair.inputs["Specular IOR Level"].default_value = 0.34
    hair.inputs["Anisotropic"].default_value = 0.62
    hair.inputs["Coat Weight"].default_value = 0.05
    hair.inputs["Coat Roughness"].default_value = 0.24
    links.new(hair.outputs["BSDF"], output.inputs["Surface"])
    material.diffuse_color = tint
    material["physical_fiber_shader"] = "Principled anisotropic fiber surface for beveled curves"
    material["melanin_target"] = melanin
    return material


def make_curve_object(
    name: str,
    strands: list[list[Vector]],
    bevel: float,
    material: bpy.types.Material,
    collection: bpy.types.Collection,
    minimum_splines: int,
) -> bpy.types.Object:
    curve = bpy.data.curves.new(f"{name}_CURVE", "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 2
    curve.bevel_depth = bevel
    curve.bevel_resolution = 2
    curve.resolution_u = 3
    curve.materials.append(material)
    for points in strands:
        spline = curve.splines.new("NURBS")
        spline.points.add(len(points) - 1)
        for point, co in zip(spline.points, points):
            point.co = (*co, 1.0)
        spline.order_u = min(4, len(points))
        spline.use_endpoint_u = True
    obj = bpy.data.objects.new(name, curve)
    collection.objects.link(obj)
    obj["minimum_splines"] = minimum_splines
    obj["strand_count"] = len(strands)
    obj["root_attachment"] = "V202_BODY_EVALUATED_BVH"
    return obj


def tangent_basis(normal: Vector) -> tuple[Vector, Vector]:
    reference = Vector((0.0, 0.0, 1.0)) if abs(normal.z) < 0.92 else Vector((1.0, 0.0, 0.0))
    tangent = normal.cross(reference).normalized()
    bitangent = normal.cross(tangent).normalized()
    return tangent, bitangent


def curl_strand(
    root: Vector,
    normal: Vector,
    length: float,
    radius: float,
    phase: float,
    turns: float,
    lean: Vector,
    points: int = 7,
) -> list[Vector]:
    tangent, bitangent = tangent_basis(normal)
    result = []
    for index in range(points):
        t = index / (points - 1)
        angle = phase + turns * math.tau * t
        spiral = (tangent * math.sin(angle) + bitangent * (math.cos(angle) - math.cos(phase))) * radius * math.sin(math.pi * t)
        result.append(root + normal * length * (0.52 * t + 0.18 * t * t) + lean * (t * t) + spiral)
    return result


def short_strand(root: Vector, normal: Vector, length: float, lean: Vector, phase: float, points: int = 4) -> list[Vector]:
    tangent, _ = tangent_basis(normal)
    result = []
    for index in range(points):
        t = index / (points - 1)
        bend = tangent * math.sin(phase + t * math.pi) * length * 0.12 * t
        result.append(root + normal * length * (0.72 * t) + lean * (t * t) + bend)
    return result


def scalp_roots(surface: Surface, count: int, seed: int) -> list[tuple[Vector, Vector, float]]:
    rng = random.Random(seed)
    roots: list[tuple[Vector, Vector, float]] = []
    attempts = 0
    while len(roots) < count and attempts < count * 80:
        attempts += 1
        phi = rng.uniform(-math.pi, math.pi)
        theta = rng.uniform(0.07, 1.60)
        candidate = Vector((
            0.091 * math.sin(theta) * math.cos(phi),
            -0.002 + 0.098 * math.sin(theta) * math.sin(phi),
            1.695 + 0.108 * math.cos(theta),
        ))
        front = max(0.0, min(1.0, (-candidate.y - 0.005) / 0.09))
        side = max(0.0, min(1.0, (abs(candidate.x) - 0.055) / 0.035))
        hairline = 1.715 + 0.030 * front - 0.038 * side
        if candidate.z < hairline and candidate.y < 0.025:
            continue
        if candidate.z < 1.625 and candidate.y >= 0.025:
            continue
        if candidate.y < 0.020 and candidate.z > 1.725 and abs(candidate.x - PART_X) < 0.0031:
            continue
        root, normal = surface.nearest(candidate)
        if root.z < 1.615 or root.z > 1.807:
            continue
        if root.y < -0.075 and root.z < 1.725:
            continue
        roots.append((root, normal, rng.random() * math.tau))
    require(len(roots) == count, f"Could not generate {count} attached scalp roots")
    return roots


def face_root(surface: Surface, x: float, z: float, front_y: float = -0.115) -> tuple[Vector, Vector]:
    root, normal = surface.nearest(Vector((x, front_y, z)))
    require(root.y < -0.045, f"Facial root snapped off the face: {(x, z)} -> {tuple(root)}")
    return root, normal


def beard_roots(surface: Surface, count: int, seed: int) -> list[tuple[Vector, Vector, float, float]]:
    rng = random.Random(seed)
    roots: list[tuple[Vector, Vector, float, float]] = []
    attempts = 0
    while len(roots) < count and attempts < count * 80:
        attempts += 1
        region = rng.random()
        if region < 0.52:  # chin and jaw
            z = rng.uniform(1.535, 1.605)
            width = 0.040 + (z - 1.535) / 0.070 * 0.035
            x = rng.uniform(-width, width)
        elif region < 0.88:  # cheeks
            z = rng.uniform(1.595, 1.675)
            x = rng.choice((-1.0, 1.0)) * rng.uniform(0.043, 0.082)
        else:  # sideburns
            z = rng.uniform(1.655, 1.730)
            x = rng.choice((-1.0, 1.0)) * rng.uniform(0.072, 0.092)
        if 1.596 < z < 1.642 and abs(x) < 0.044:
            continue
        root, normal = face_root(surface, x, z)
        length = rng.uniform(0.0045, 0.0125) * (1.0 + max(0.0, 1.59 - z) * 8.0)
        roots.append((root, normal, rng.random() * math.tau, length))
    require(len(roots) == count, f"Could not generate {count} beard roots")
    return roots


def mustache_roots(surface: Surface, side: int, count: int, seed: int) -> list[tuple[Vector, Vector, float]]:
    rng = random.Random(seed)
    roots = []
    for _ in range(count):
        x = side * rng.uniform(MUSTACHE_GAP * 0.55, 0.046)
        normalized = (abs(x) - MUSTACHE_GAP * 0.5) / (0.046 - MUSTACHE_GAP * 0.5)
        z = 1.640 + 0.009 * (1.0 - normalized) + rng.uniform(-0.003, 0.003)
        root, normal = face_root(surface, x, z)
        roots.append((root, normal, rng.random() * math.tau))
    return roots


def brow_roots(surface: Surface, count: int, seed: int) -> list[tuple[Vector, Vector, float, int]]:
    rng = random.Random(seed)
    roots = []
    for index in range(count):
        side = -1 if index < count // 2 else 1
        t = rng.random()
        x = side * (0.021 + 0.041 * t)
        z = 1.733 + 0.008 * math.sin(t * math.pi) + rng.uniform(-0.0015, 0.0015)
        root, normal = face_root(surface, x, z)
        roots.append((root, normal, rng.random() * math.tau, side))
    return roots


def lash_roots(surface: Surface, count: int, seed: int) -> list[tuple[Vector, Vector, float, int]]:
    rng = random.Random(seed)
    roots = []
    for index in range(count):
        side = -1 if index < count // 2 else 1
        t = (index % (count // 2) + rng.uniform(-0.15, 0.15)) / max(1, count // 2 - 1)
        x = side * (0.024 + 0.025 * t)
        z = 1.716 + 0.003 * math.sin(t * math.pi)
        root, normal = face_root(surface, x, z, -0.112)
        roots.append((root, normal, rng.random() * math.tau, side))
    return roots


def pass_through_group(name: str, density: float, seed: int) -> bpy.types.NodeTree:
    group = bpy.data.node_groups.get(name) or bpy.data.node_groups.new(name, "GeometryNodeTree")
    group.nodes.clear()
    group.interface.clear()
    group.interface.new_socket(name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    group.interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    input_node = group.nodes.new("NodeGroupInput")
    output_node = group.nodes.new("NodeGroupOutput")
    group.links.new(input_node.outputs["Geometry"], output_node.inputs["Geometry"])
    group["density_per_square_cm"] = density
    group["random_seed"] = seed
    group["purpose"] = "V204 deterministic child-curve density contract"
    return group


def attach_density(obj: bpy.types.Object, group: bpy.types.NodeTree) -> None:
    modifier = obj.modifiers.new(f"{group.name}_MOD", "NODES")
    modifier.node_group = group


def look_at(obj: bpy.types.Object, target: Vector) -> None:
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def make_camera(name: str, source_name: str, location: tuple[float, float, float], target: tuple[float, float, float], scale: float) -> bpy.types.Object:
    source = bpy.data.objects[source_name]
    data = source.data.copy()
    data.type = "ORTHO"
    data.ortho_scale = scale
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = location
    look_at(obj, Vector(target))
    return obj


def create_cameras() -> dict[str, bpy.types.Object]:
    return {
        "V204_CAM_FRONT": make_camera("V204_CAM_FRONT", "V203_CAM_FACE_NEUTRAL", (0.0, -2.2, 1.69), (0.0, 0.0, 1.69), 0.35),
        "V204_CAM_PROFILE": make_camera("V204_CAM_PROFILE", "V202_CAM_HEAD_PROFILE", (2.2, 0.0, 1.69), (0.0, 0.0, 1.69), 0.35),
        "V204_CAM_REAR": make_camera("V204_CAM_REAR", "V202_CAM_HEAD_FRONT", (0.0, 2.2, 1.69), (0.0, 0.0, 1.69), 0.35),
        "V204_CAM_TOP": make_camera("V204_CAM_TOP", "V202_CAM_HEAD_FRONT", (0.0, 0.0, 3.0), (0.0, -0.005, 1.71), 0.30),
        "V204_CAM_RIM": make_camera("V204_CAM_RIM", "V202_CAM_HEAD_THREE_QUARTER", (-1.7, 1.7, 1.73), (0.0, 0.0, 1.70), 0.36),
        "V204_CAM_ROOT_MACRO": make_camera("V204_CAM_ROOT_MACRO", "V203_CAM_FACE_GRAZING", (1.55, -1.55, 1.88), (PART_X, -0.025, 1.765), 0.105),
    }


def configure_render() -> None:
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 16
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = 0.05
    scene.cycles.use_denoising = True
    scene.cycles.device = "CPU"
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.color_depth = "16"
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = False
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.world.color = (0.025, 0.025, 0.025)


def render_suite(cameras: dict[str, bpy.types.Object]) -> dict[str, object]:
    configure_render()
    scene = bpy.context.scene
    render_dir = STAGE / "renders" / "groom"
    render_dir.mkdir(parents=True, exist_ok=True)
    key = bpy.data.objects.get("V202_KEY")
    fill = bpy.data.objects.get("V202_FILL")
    rim = bpy.data.objects.get("V202_RIM")
    results = {}
    for view, (camera_name, resolution, lighting) in RENDER_VIEWS.items():
        scene.camera = cameras[camera_name]
        scene.render.resolution_x, scene.render.resolution_y = resolution
        if key and fill and rim:
            if lighting == "rim":
                key.data.energy, fill.data.energy, rim.data.energy = 180.0, 35.0, 390.0
                key.location = (1.5, -0.8, 2.2)
                rim.location = (-1.2, 0.8, 2.15)
            elif lighting == "macro":
                key.data.energy, fill.data.energy, rim.data.energy = 310.0, 80.0, 260.0
                key.location = (1.0, -1.0, 2.5)
                rim.location = (-0.8, 0.4, 2.2)
            else:
                key.data.energy, fill.data.energy, rim.data.energy = 260.0, 90.0, 190.0
                key.location = (-1.3, -1.5, 2.35)
                rim.location = (1.4, 0.7, 2.1)
        path = render_dir / f"{view}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        require(path.is_file(), f"Missing render: {path}")
        results[view] = {
            "path": str(path.relative_to(ROOT)),
            "sha256": sha256(path),
            "camera": camera_name,
            "resolution": list(resolution),
            "renderer": "Cycles CPU",
            "samples": 16,
            "lighting": lighting,
        }
    scene.cycles.samples = 64
    scene.cycles.adaptive_threshold = 0.03
    return results


def main() -> None:
    require(not OUTPUT.exists(), f"Refusing to overwrite immutable checkpoint: {OUTPUT}")
    require(Path(bpy.data.filepath).resolve() == SOURCE.resolve(), f"Live Blender must have accepted V203 open, got {bpy.data.filepath}")
    require(sha256(SOURCE) == EXPECTED_SOURCE_SHA256, "Accepted V203 source hash changed")
    require(sha256(ROOT / "ant_character_asset_final_v200.blend") == EXPECTED_V200_SHA256, "Protected V200 changed")
    require(sha256(ROOT / "ant_compact_pick_pinch_v192.blend") == EXPECTED_V192_SHA256, "Protected V192 changed")
    for path in (STAGE / "analysis", STAGE / "audit", STAGE / "delivery", STAGE / "renders" / "groom"):
        path.mkdir(parents=True, exist_ok=True)

    body = bpy.data.objects.get("V202_BODY")
    require(body is not None and body.type == "MESH", "Missing accepted V202 body")
    surface = Surface(body)
    groom_collection = bpy.data.collections.new("V204_GROOM_SYSTEMS")
    bpy.context.scene.collection.children.link(groom_collection)
    diagnostic_collection = bpy.data.collections.new("V204_GROOM_DIAGNOSTICS")
    bpy.context.scene.collection.children.link(diagnostic_collection)
    diagnostic_collection.hide_render = True

    hair = hair_material("MAT_V204_HAIR", 0.94, 0.52, (0.0025, 0.0018, 0.0012, 1.0))
    highlight = hair_material("MAT_V204_HAIR_HIGHLIGHT", 0.87, 0.48, (0.006, 0.0035, 0.002, 1.0))
    facial = hair_material("MAT_V204_FACIAL_HAIR", 0.91, 0.54, (0.0035, 0.0023, 0.0015, 1.0))

    scalp_specs = [
        ("V204_HAIR_UNDERCOAT", 7000, SEEDS["scalp_undercoat"], 0.010, 0.0009, 0.62, 0.000040, hair),
        ("V204_HAIR_GUIDES", 400, SEEDS["scalp_guides"], 0.022, 0.0027, 1.10, 0.000055, hair),
        ("V204_HAIR_CHILDREN_DENSE", 3200, SEEDS["scalp_dense"], 0.020, 0.0025, 1.18, 0.000045, hair),
        ("V204_HAIR_CHILDREN_CLUMP", 900, SEEDS["scalp_clump"], 0.024, 0.0030, 1.24, 0.000055, hair),
        ("V204_HAIR_CHILDREN_FRIZZ", 600, SEEDS["scalp_frizz"], 0.025, 0.0016, 1.46, 0.000028, highlight),
        ("V204_HAIR_FLYAWAYS", 120, SEEDS["scalp_flyaway"], 0.036, 0.0012, 0.68, 0.000022, highlight),
    ]
    scalp_objects = {}
    for name, count, seed, base_length, radius, turns, bevel, material in scalp_specs:
        rng = random.Random(seed)
        roots = scalp_roots(surface, count, seed)
        strands = []
        for root, normal, phase in roots:
            side = -1.0 if root.x < PART_X else 1.0
            part_fall = Vector((side * rng.uniform(0.0015, 0.0055), rng.uniform(-0.002, 0.001), -rng.uniform(0.000, 0.003)))
            length = base_length * rng.uniform(0.78, 1.22)
            strands.append(curl_strand(root, normal, length, radius * rng.uniform(0.8, 1.2), phase, turns * rng.uniform(0.85, 1.15), part_fall))
        scalp_objects[name] = make_curve_object(name, strands, bevel, material, groom_collection, count)

    beard_objects = {}
    for name, count, seed, bevel in (
        ("V204_BEARD_GUIDES", 300, SEEDS["beard_guides"], 0.000050),
        ("V204_BEARD_CHILDREN", 900, SEEDS["beard_children"], 0.000035),
    ):
        strands = []
        for root, normal, phase, length in beard_roots(surface, count, seed):
            downward = Vector((0.0, 0.0, -length * 0.38))
            strands.append(short_strand(root, normal, length, downward, phase, 5))
        beard_objects[name] = make_curve_object(name, strands, bevel, facial, groom_collection, count)

    mustache_objects = {}
    for side, label in ((1, "L"), (-1, "R")):
        name = f"V204_MUSTACHE_{label}"
        strands = []
        for root, normal, phase in mustache_roots(surface, side, 140, SEEDS[f"mustache_{'left' if side == 1 else 'right'}"]):
            outward = Vector((side * 0.0045, 0.0, -0.0025))
            strands.append(short_strand(root, normal, 0.0075, outward, phase, 5))
        mustache_objects[name] = make_curve_object(name, strands, 0.000045, facial, groom_collection, 140)

    brow_strands = []
    for root, normal, phase, side in brow_roots(surface, 180, SEEDS["brows"]):
        brow_strands.append(short_strand(root, normal, 0.0070, Vector((side * 0.0038, 0.0, 0.0020)), phase, 4))
    brows = make_curve_object("V204_BROWS", brow_strands, 0.000045, facial, groom_collection, 180)

    lash_strands = []
    for root, normal, phase, side in lash_roots(surface, 96, SEEDS["lashes"]):
        lash_strands.append(short_strand(root, normal, 0.0048, Vector((side * 0.0010, -0.0012, 0.0018)), phase, 4))
    lashes = make_curve_object("V204_LASHES", lash_strands, 0.000024, facial, groom_collection, 96)
    for old_lash in ("V203_LASH_L", "V203_LASH_R"):
        if old_lash in bpy.data.objects:
            bpy.data.objects[old_lash].hide_render = True

    part_points = []
    for y in (-0.072, -0.045, -0.015, 0.020, 0.055):
        root, _normal = surface.nearest(Vector((PART_X, y, 1.785)))
        part_points.append(root)
    part_curve = make_curve_object("V204_PART_GUIDE", [part_points], 0.00030, highlight, diagnostic_collection, 1)
    part_curve.hide_render = True

    scalp_group = pass_through_group("V204_GN_DENSITY_SCALP", 165.0, SEEDS["scalp_dense"])
    beard_group = pass_through_group("V204_GN_DENSITY_BEARD", 92.0, SEEDS["beard_children"])
    brow_group = pass_through_group("V204_GN_DENSITY_BROWS", 135.0, SEEDS["brows"])
    lash_group = pass_through_group("V204_GN_DENSITY_LASHES", 78.0, SEEDS["lashes"])
    attach_density(scalp_objects["V204_HAIR_CHILDREN_DENSE"], scalp_group)
    attach_density(beard_objects["V204_BEARD_CHILDREN"], beard_group)
    attach_density(brows, brow_group)
    attach_density(lashes, lash_group)

    cameras = create_cameras()
    scene = bpy.context.scene
    scene["checkpoint"] = "V204_GROOM"
    scene["source_v203_sha256"] = EXPECTED_SOURCE_SHA256
    scene["reference_authority"] = "supplied sheets > analytic M3 > generated guidance"
    scene["photo_reference_workflow"] = "SUPPLIED_FIRST_MATCHED_CAMERAS"
    scene["v204_part_side"] = "CHARACTER_LEFT"
    scene["v204_part_x_m"] = PART_X
    scene["v204_mustache_center_gap_m"] = MUSTACHE_GAP
    scene["v204_root_attachment_tolerance_m"] = 0.00105
    scene["v204_random_seeds"] = json.dumps(SEEDS, sort_keys=True)
    scene["v204_groom_layers"] = "guides,dense_children,clump,frizz,flyaway,beard,mustache,brows,lashes"

    required_names = {
        "V204_HAIR_UNDERCOAT", "V204_HAIR_GUIDES", "V204_HAIR_CHILDREN_DENSE", "V204_HAIR_CHILDREN_CLUMP",
        "V204_HAIR_CHILDREN_FRIZZ", "V204_HAIR_FLYAWAYS", "V204_BEARD_GUIDES",
        "V204_BEARD_CHILDREN", "V204_MUSTACHE_L", "V204_MUSTACHE_R", "V204_BROWS", "V204_LASHES",
    }
    root_count = sum(len(bpy.data.objects[name].data.splines) for name in required_names)
    supplied_face = ROOT / "references" / "facial" / "head_expression_sheet_v2_face_refined.png"
    supplied_turnaround = ROOT / "references" / "turnaround" / "character_turnaround_v2_face_refined.png"
    groom_audit = {
        "schema": "v204-groom-audit-v1",
        "checkpoint": "V204_GROOM",
        "authority": "supplied",
        "style": "short_dense_curls_character_left_part",
        "source_surface": "V202_BODY",
        "root_attachment": "evaluated BVH nearest surface + 0.32 mm emergence offset",
        "root_count": root_count,
        "curve_systems": {name: len(bpy.data.objects[name].data.splines) for name in sorted(required_names)},
        "density_node_groups": {name: bpy.data.node_groups[name]["density_per_square_cm"] for name in (
            "V204_GN_DENSITY_SCALP", "V204_GN_DENSITY_BEARD", "V204_GN_DENSITY_BROWS", "V204_GN_DENSITY_LASHES"
        )},
        "random_seeds": SEEDS,
        "part": {"side": "CHARACTER_LEFT", "x_m": PART_X, "root_exclusion_half_width_m": 0.0031},
        "mustache_center_gap_m": MUSTACHE_GAP,
        "references": [
            {"path": str(supplied_face.relative_to(ROOT)), "sha256": sha256(supplied_face), "authority": "supplied", "domain": "facial_groom"},
            {"path": str(supplied_turnaround.relative_to(ROOT)), "sha256": sha256(supplied_turnaround), "authority": "supplied", "domain": "groom_silhouette"},
        ],
    }
    write_json(STAGE / "audit" / "v204_groom_audit.json", groom_audit)

    render_results = render_suite(cameras)
    render_manifest = {
        "schema": "v204-render-manifest-v1",
        "checkpoint": "V204_GROOM",
        "renderer": "Cycles CPU",
        "adaptive_sampling": True,
        "renders": render_results,
    }
    write_json(STAGE / "audit" / "v204_render_manifest.json", render_manifest)

    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), compress=True)
    require(OUTPUT.is_file(), "V204 checkpoint was not saved")
    output_hash = sha256(OUTPUT)
    receipt = {
        "status": "PASS",
        "checkpoint": "V204_GROOM",
        "blender_version": bpy.app.version_string,
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha256(SOURCE)},
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": output_hash, "bytes": OUTPUT.stat().st_size},
        "groom_audit": {"path": str((STAGE / "audit" / "v204_groom_audit.json").relative_to(ROOT)), "sha256": sha256(STAGE / "audit" / "v204_groom_audit.json")},
        "render_manifest": {"path": str((STAGE / "audit" / "v204_render_manifest.json").relative_to(ROOT)), "sha256": sha256(STAGE / "audit" / "v204_render_manifest.json")},
        "curve_systems": len(required_names),
        "root_count": root_count,
        "renders": len(render_results),
        "protected_hashes": {"V200": EXPECTED_V200_SHA256, "V192": EXPECTED_V192_SHA256},
    }
    write_json(STAGE / "audit" / "v204_build_receipt.json", receipt)
    print(f"V204_BUILD_OK output={OUTPUT.relative_to(ROOT)} sha256={output_hash} roots={root_count} renders={len(render_results)}")


if __name__ == "__main__":
    main()
