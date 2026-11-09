"""Build explicit tapered trouser closures and Chelsea boot assemblies on V242."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v242_tailoring_collar" / "Character_An_tailored_wardrobe_v242.blend"
STAGE = ROOT / "production_v243_trousers_boots"
OUTPUT = STAGE / "Character_An_trousers_boots_v243.blend"
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


def move_to_collection(obj: bpy.types.Object, collection: bpy.types.Collection) -> None:
    for owner in tuple(obj.users_collection):
        owner.objects.unlink(obj)
    collection.objects.link(obj)


def material(name: str, color: tuple[float, float, float, float], roughness: float, metallic: float = 0.0) -> bpy.types.Material:
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.28
    return mat


def finish_mesh(obj: bpy.types.Object, mat: bpy.types.Material) -> bpy.types.Object:
    obj.data.materials.append(mat)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    return obj


def rounded_box(name: str, location: tuple[float, float, float], dimensions: tuple[float, float, float], radius: float, collection: bpy.types.Collection, mat: bpy.types.Material) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    move_to_collection(obj, collection)
    obj.dimensions = dimensions
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bevel = obj.modifiers.new(name + "_BEVEL", "BEVEL")
    bevel.width = radius
    bevel.segments = 5
    bevel.limit_method = "ANGLE"
    weighted = obj.modifiers.new(name + "_SMOOTH_NORMAL", "WEIGHTED_NORMAL")
    weighted.keep_sharp = True
    return finish_mesh(obj, mat)


def elliptical_band(name: str, center: tuple[float, float, float], radii: tuple[float, float], height: float, collection: bpy.types.Collection, mat: bpy.types.Material, segments: int = 64) -> bpy.types.Object:
    cx, cy, cz = center
    rx, ry = radii
    inner = 0.88
    vertices = []
    for z, scale in ((cz - height / 2, 1.0), (cz + height / 2, 1.0), (cz - height / 2, inner), (cz + height / 2, inner)):
        for i in range(segments):
            angle = 2.0 * math.pi * i / segments
            vertices.append((cx + rx * scale * math.cos(angle), cy + ry * scale * math.sin(angle), z))
    faces = []
    for i in range(segments):
        j = (i + 1) % segments
        faces.extend([
            (i, j, segments + j, segments + i),
            (2 * segments + i, 3 * segments + i, 3 * segments + j, 2 * segments + j),
            (segments + i, segments + j, 3 * segments + j, 3 * segments + i),
            (i, 2 * segments + i, 2 * segments + j, j),
        ])
    mesh = bpy.data.meshes.new(name + "_MESH")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    bevel = obj.modifiers.new(name + "_EDGE_SOFTEN", "BEVEL")
    bevel.width = 0.003
    bevel.segments = 3
    return finish_mesh(obj, mat)


def bone_parent(obj: bpy.types.Object, bone: str) -> None:
    rig = bpy.data.objects[RIG_NAME]
    world = obj.matrix_world.copy()
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = bone
    obj.matrix_world = world


def build_boot(side: str, x: float, collection: bpy.types.Collection, leather: bpy.types.Material, sole_mat: bpy.types.Material, gore_mat: bpy.types.Material) -> list[bpy.types.Object]:
    sign = 1.0 if x > 0 else -1.0
    pieces = [
        rounded_box(f"V243_BOOT_FOOT_{side}", (x, -0.052, 0.078), (0.160, 0.282, 0.105), 0.038, collection, leather),
        rounded_box(f"V243_BOOT_SHAFT_{side}", (x, 0.006, 0.190), (0.148, 0.170, 0.205), 0.026, collection, leather),
        rounded_box(f"V243_BOOT_SOLE_{side}", (x, -0.054, 0.022), (0.174, 0.302, 0.030), 0.009, collection, sole_mat),
        rounded_box(f"V243_BOOT_HEEL_{side}", (x, 0.070, 0.042), (0.145, 0.075, 0.048), 0.008, collection, sole_mat),
        rounded_box(f"V243_BOOT_GORE_OUTER_{side}", (x + sign * 0.075, 0.000, 0.210), (0.006, 0.090, 0.082), 0.003, collection, gore_mat),
        rounded_box(f"V243_BOOT_GORE_INNER_{side}", (x - sign * 0.075, 0.000, 0.210), (0.006, 0.090, 0.082), 0.003, collection, gore_mat),
        rounded_box(f"V243_BOOT_PULL_TAB_{side}", (x, 0.080, 0.304), (0.026, 0.010, 0.064), 0.003, collection, leather),
    ]
    for obj in pieces:
        obj["v243_boot_component"] = True
        bone_parent(obj, f"foot_fk.{side}")
    return pieces


def point_at(obj: bpy.types.Object, target: Vector) -> None:
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def main() -> None:
    if Path(bpy.data.filepath).resolve() != SOURCE.resolve():
        raise RuntimeError(f"Open V242 first: {SOURCE}")
    STAGE.mkdir(parents=True, exist_ok=True)
    RENDERS.mkdir(parents=True, exist_ok=True)
    AUDIT.mkdir(parents=True, exist_ok=True)
    old_boots = bpy.data.objects.get("V241_BOOT_SHELLS")
    if old_boots:
        old_boots.hide_render = True
        old_boots.hide_viewport = True
    body = bpy.data.objects.get("V211_BODY_NEUTRAL")
    if body:
        keep = body.vertex_groups.get("V243_BODY_ABOVE_BOOTS") or body.vertex_groups.new(name="V243_BODY_ABOVE_BOOTS")
        keep_indices = [vertex.index for vertex in body.data.vertices if (body.matrix_world @ vertex.co).z >= 0.255]
        keep.add(keep_indices, 1.0, "REPLACE")
        mask = body.modifiers.get("V243_LOWER_FOOT_MASK") or body.modifiers.new("V243_LOWER_FOOT_MASK", "MASK")
        mask.vertex_group = keep.name

    collection = ensure_collection("V243_TROUSERS_BOOTS")
    trouser_mat = material("MAT_V243_TROUSER_DETAIL", (0.012, 0.011, 0.012, 1.0), 0.72)
    leather = material("MAT_V243_BROWN_LEATHER", (0.105, 0.025, 0.010, 1.0), 0.40)
    sole_mat = material("MAT_V243_DARK_SOLE", (0.016, 0.010, 0.008, 1.0), 0.58)
    gore_mat = material("MAT_V243_ELASTIC_GORE", (0.020, 0.018, 0.016, 1.0), 0.84)

    pieces = []
    waistband = elliptical_band("V243_TROUSER_WAISTBAND", (0.0, 0.0, 0.920), (0.252, 0.158), 0.035, collection, trouser_mat)
    bone_parent(waistband, "hips")
    pieces.append(waistband)
    for side, x in (("L", -0.165), ("R", 0.165)):
        cuff = elliptical_band(f"V243_ROLLED_CUFF_{side}", (x, 0.008, 0.292), (0.096, 0.082), 0.050, collection, trouser_mat)
        bone_parent(cuff, f"shin_fk.{side}")
        pieces.append(cuff)
        pieces.extend(build_boot(side, x, collection, leather, sole_mat, gore_mat))

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.look = "AgX - Medium High Contrast"
    camera = bpy.data.objects["CAM_V211_FRONT"]
    camera.data.type = "PERSP"
    views = {
        "front": (Vector((0.0, -3.75, 1.00)), Vector((0.0, 0.0, 0.98)), 66.0, (900, 1000)),
        "three_quarter": (Vector((-2.65, -2.75, 1.10)), Vector((0.0, 0.0, 1.00)), 70.0, (900, 1000)),
        "boots": (Vector((-0.78, -1.62, 0.28)), Vector((0.0, -0.02, 0.19)), 78.0, (1100, 750)),
    }
    render_records = {}
    for label, (location, target, lens, resolution) in views.items():
        camera.location = location
        camera.data.lens = lens
        point_at(camera, target)
        scene.camera = camera
        scene.render.resolution_x, scene.render.resolution_y = resolution
        scene.render.resolution_percentage = 100
        path = RENDERS / f"v243_{label}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        render_records[label] = {"path": str(path.relative_to(ROOT)), "sha256": sha256(path)}

    scene["V243_STATUS"] = "EXPLICIT_TROUSER_CLOSURES_AND_CHELSEA_BOOTS"
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v243-trousers-boots-v1",
        "status": "BUILT_VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha256(SOURCE)},
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha256(OUTPUT)},
        "hidden": [old_boots.name] if old_boots else [],
        "pieces": [obj.name for obj in pieces],
        "renders": render_records,
    }
    (AUDIT / "v243_manifest.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("V243_TROUSERS_BOOTS_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
