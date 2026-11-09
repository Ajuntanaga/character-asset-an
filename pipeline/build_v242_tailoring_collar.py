"""Tailor V241 with clean visible garment edges and a neck-seam closure."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v241_rigged_wardrobe_foundation" / "Character_An_rigged_wardrobe_v241.blend"
STAGE = ROOT / "production_v242_tailoring_collar"
OUTPUT = STAGE / "Character_An_tailored_wardrobe_v242.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"
RIG_NAME = "V239_CLEAN_CHARACTER_RIG"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def ensure_collection(name: str) -> bpy.types.Collection:
    collection = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if collection.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(collection)
    return collection


def material(name: str, color: tuple[float, float, float, float], roughness: float) -> bpy.types.Material:
    value = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    value.use_nodes = True
    bsdf = value.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = 0.0
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.25
    if "Coat Weight" in bsdf.inputs:
        bsdf.inputs["Coat Weight"].default_value = 0.05
    return value


def tune_existing_materials() -> None:
    jacket = bpy.data.materials.get("MAT_V241_CHARCOAL_JACKET")
    if jacket and jacket.use_nodes:
        bsdf = jacket.node_tree.nodes.get("Principled BSDF")
        bsdf.inputs["Base Color"].default_value = (0.009, 0.010, 0.012, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.82
        if "Specular IOR Level" in bsdf.inputs:
            bsdf.inputs["Specular IOR Level"].default_value = 0.22
        if "Coat Weight" in bsdf.inputs:
            bsdf.inputs["Coat Weight"].default_value = 0.04
    boots = bpy.data.materials.get("MAT_V241_BOOTS")
    if boots and boots.use_nodes:
        boots.node_tree.nodes.get("Principled BSDF").inputs["Roughness"].default_value = 0.47


def mesh_object(
    name: str,
    vertices: list[tuple[float, float, float]],
    faces: list[tuple[int, ...]],
    collection: bpy.types.Collection,
    mat: bpy.types.Material,
    thickness: float = 0.0025,
) -> bpy.types.Object:
    mesh = bpy.data.meshes.new(name + "_MESH")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    obj.data.materials.append(mat)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    if thickness:
        solidify = obj.modifiers.new(name + "_THICKNESS", "SOLIDIFY")
        solidify.thickness = thickness
        solidify.offset = 0.0
    bevel = obj.modifiers.new(name + "_EDGE_SOFTEN", "BEVEL")
    bevel.width = 0.0035
    bevel.segments = 3
    return obj


def bone_parent(obj: bpy.types.Object, bone: str = "chest") -> None:
    rig = bpy.data.objects[RIG_NAME]
    world = obj.matrix_world.copy()
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = bone
    obj.matrix_world = world
    obj["v242_rigid_chest_detail"] = True


def curve_object(
    name: str,
    points: list[tuple[float, float, float]],
    collection: bpy.types.Collection,
    mat: bpy.types.Material,
    bevel: float,
) -> bpy.types.Object:
    curve = bpy.data.curves.new(name + "_CURVE", "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 16
    curve.bevel_depth = bevel
    curve.bevel_resolution = 4
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for point, co in zip(spline.bezier_points, points):
        point.co = co
        point.handle_left_type = "AUTO"
        point.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(name, curve)
    collection.objects.link(obj)
    obj.data.materials.append(mat)
    return obj


def build_front_panel(collection: bpy.types.Collection, mat: bpy.types.Material) -> bpy.types.Object:
    # Smooth fitted inset over the raw body-derived shirt opening.
    sections = [
        (-0.105, 0.105, -0.161, 0.895),
        (-0.120, 0.120, -0.179, 1.010),
        (-0.145, 0.145, -0.202, 1.145),
        (-0.165, 0.165, -0.213, 1.285),
        (-0.130, 0.130, -0.173, 1.405),
    ]
    vertices = []
    for left, right, y, z in sections:
        vertices.extend([(left, y, z), (right, y, z)])
    faces = [(row * 2, row * 2 + 1, row * 2 + 3, row * 2 + 2) for row in range(len(sections) - 1)]
    return mesh_object("V242_CLEAN_SHIRT_INSET", vertices, faces, collection, mat, 0.0032)


def build_lapel(name: str, sign: float, collection: bpy.types.Collection, mat: bpy.types.Material) -> bpy.types.Object:
    # A six-quad ribbon covers the jagged procedural opening and establishes a
    # deliberate jacket line from collar to waist.
    inner = [
        (0.055 * sign, -0.151, 1.455),
        (0.083 * sign, -0.188, 1.370),
        (0.105 * sign, -0.218, 1.255),
        (0.112 * sign, -0.208, 1.120),
        (0.112 * sign, -0.180, 0.980),
        (0.120 * sign, -0.158, 0.895),
    ]
    outer = [
        (0.135 * sign, -0.142, 1.442),
        (0.188 * sign, -0.171, 1.350),
        (0.196 * sign, -0.190, 1.245),
        (0.184 * sign, -0.187, 1.115),
        (0.178 * sign, -0.168, 0.985),
        (0.175 * sign, -0.149, 0.895),
    ]
    vertices = [co for pair in zip(inner, outer) for co in pair]
    faces = [(i * 2, i * 2 + 1, i * 2 + 3, i * 2 + 2) for i in range(len(inner) - 1)]
    return mesh_object(name, vertices, faces, collection, mat, 0.0045)


def build_collar(collection: bpy.types.Collection, mat: bpy.types.Material) -> bpy.types.Object:
    # Elliptical standing collar closes the V240 head/body transition.
    segments = 64
    outer_x, outer_y = 0.132, 0.113
    inner_x, inner_y = 0.102, 0.086
    z0, z1 = 1.430, 1.469
    vertices = []
    for z, rx, ry in ((z0, outer_x, outer_y), (z1, outer_x, outer_y), (z0, inner_x, inner_y), (z1, inner_x, inner_y)):
        for i in range(segments):
            angle = 2.0 * math.pi * i / segments
            vertices.append((rx * math.cos(angle), ry * math.sin(angle) - 0.006, z))
    faces = []
    for i in range(segments):
        j = (i + 1) % segments
        outer_bottom, outer_top = i, segments + i
        inner_bottom, inner_top = 2 * segments + i, 3 * segments + i
        faces.extend([
            (outer_bottom, j, segments + j, outer_top),
            (inner_bottom, inner_top, 3 * segments + j, 2 * segments + j),
            (outer_top, segments + j, 3 * segments + j, inner_top),
        ])
    return mesh_object("V242_STANDING_SHIRT_COLLAR", vertices, faces, collection, mat, 0.0)


def build_hem(collection: bpy.types.Collection, mat: bpy.types.Material) -> bpy.types.Object:
    points = [
        (-0.205, -0.146, 0.900),
        (-0.130, -0.164, 0.887),
        (0.0, -0.170, 0.882),
        (0.130, -0.164, 0.887),
        (0.205, -0.146, 0.900),
    ]
    return curve_object("V242_JACKET_HEM_SEAM", points, collection, mat, 0.004)


def build_shoulder_yoke(name: str, sign: float, collection: bpy.types.Collection, mat: bpy.types.Material) -> bpy.types.Object:
    vertices = [
        (0.078 * sign, -0.105, 1.462),
        (0.150 * sign, -0.150, 1.455),
        (0.285 * sign, -0.128, 1.425),
        (0.355 * sign, -0.072, 1.392),
        (0.332 * sign, -0.098, 1.355),
        (0.245 * sign, -0.162, 1.385),
        (0.135 * sign, -0.174, 1.405),
        (0.082 * sign, -0.126, 1.425),
    ]
    return mesh_object(name, vertices, [tuple(range(8))], collection, mat, 0.004)


def point_at(obj: bpy.types.Object, target: Vector) -> None:
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def main() -> None:
    if Path(bpy.data.filepath).resolve() != SOURCE.resolve():
        raise RuntimeError(f"Open V241 first: {SOURCE}")
    STAGE.mkdir(parents=True, exist_ok=True)
    RENDERS.mkdir(parents=True, exist_ok=True)
    AUDIT.mkdir(parents=True, exist_ok=True)
    tune_existing_materials()
    collection = ensure_collection("V242_TAILORING_DETAILS")
    shirt_mat = material("MAT_V242_FLORAL_GROUND", (0.050, 0.018, 0.012, 1.0), 0.58)
    jacket_mat = material("MAT_V242_LAPEL_CHARCOAL", (0.012, 0.014, 0.017, 1.0), 0.68)
    trim_mat = material("MAT_V242_EDGE_TRIM", (0.024, 0.020, 0.020, 1.0), 0.72)

    details = [
        build_front_panel(collection, shirt_mat),
        build_lapel("V242_LAPEL_L", -1.0, collection, jacket_mat),
        build_lapel("V242_LAPEL_R", 1.0, collection, jacket_mat),
        build_collar(collection, shirt_mat),
        build_hem(collection, trim_mat),
    ]
    shoulder_paths = {
        "V242_SHOULDER_SEAM_L": [(-0.082, -0.110, 1.458), (-0.160, -0.145, 1.455), (-0.265, -0.125, 1.430), (-0.345, -0.060, 1.395)],
        "V242_SHOULDER_SEAM_R": [(0.082, -0.110, 1.458), (0.160, -0.145, 1.455), (0.265, -0.125, 1.430), (0.345, -0.060, 1.395)],
    }
    for name, points in shoulder_paths.items():
        details.append(curve_object(name, points, collection, jacket_mat, 0.010))
    for name, sign in (("V242_OPENING_PIPING_L", -1.0), ("V242_OPENING_PIPING_R", 1.0)):
        details.append(curve_object(name, [(0.06 * sign, -0.157, 1.45), (0.095 * sign, -0.215, 1.27), (0.115 * sign, -0.184, 0.90)], collection, trim_mat, 0.004))
    for obj in details:
        bone_parent(obj)

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.look = "AgX - Medium High Contrast"
    camera = bpy.data.objects["CAM_V211_FRONT"]
    camera.data.type = "PERSP"
    views = {
        "front": (Vector((0.0, -3.75, 1.00)), Vector((0.0, 0.0, 0.98)), 66.0, (900, 1000)),
        "three_quarter": (Vector((-2.65, -2.75, 1.10)), Vector((0.0, 0.0, 1.00)), 70.0, (900, 1000)),
        "upper": (Vector((0.0, -2.05, 1.30)), Vector((0.0, 0.0, 1.26)), 76.0, (900, 1000)),
    }
    render_records = {}
    for label, (location, look, lens, resolution) in views.items():
        camera.location = location
        camera.data.lens = lens
        point_at(camera, look)
        scene.camera = camera
        scene.render.resolution_x, scene.render.resolution_y = resolution
        scene.render.resolution_percentage = 100
        path = RENDERS / f"v242_{label}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        render_records[label] = {"path": str(path.relative_to(ROOT)), "sha256": sha256(path)}

    scene["V242_STATUS"] = "TAILORED_VISIBLE_EDGES_AND_NECK_SEAM_CLOSURE"
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v242-tailoring-collar-v1",
        "status": "BUILT_VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha256(SOURCE)},
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha256(OUTPUT)},
        "details": [obj.name for obj in details],
        "renders": render_records,
    }
    (AUDIT / "v242_manifest.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("V242_TAILORING_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
