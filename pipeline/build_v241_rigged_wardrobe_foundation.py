"""Build rigged body-derived wardrobe shells on the accepted V240 character."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v240_identity_clean_rig" / "Character_An_identity_clean_rig_v240.blend"
STAGE = ROOT / "production_v241_rigged_wardrobe_foundation"
OUTPUT = STAGE / "Character_An_rigged_wardrobe_v241.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"


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


def material(name: str, base: tuple[float, float, float, float], roughness: float, metallic: float = 0.0) -> bpy.types.Material:
    value = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    value.use_nodes = True
    bsdf = value.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = base
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return value


def floral_material() -> bpy.types.Material:
    value = material("MAT_V241_FLORAL_SHIRT", (0.055, 0.025, 0.018, 1.0), 0.52)
    nodes = value.node_tree.nodes
    links = value.node_tree.links
    for node in tuple(nodes):
        if node.type not in {"BSDF_PRINCIPLED", "OUTPUT_MATERIAL"}:
            nodes.remove(node)
    bsdf = nodes.get("Principled BSDF")
    texcoord = nodes.new("ShaderNodeTexCoord")
    mapping = nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (15.0, 15.0, 15.0)
    voronoi = nodes.new("ShaderNodeTexVoronoi")
    voronoi.distance = "EUCLIDEAN"
    voronoi.feature = "DISTANCE_TO_EDGE"
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 6.0
    noise.inputs["Detail"].default_value = 4.0
    mix = nodes.new("ShaderNodeMixRGB")
    mix.blend_type = "MULTIPLY"
    mix.inputs[0].default_value = 0.72
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.20
    ramp.color_ramp.elements[0].color = (0.015, 0.008, 0.006, 1.0)
    ramp.color_ramp.elements[1].position = 0.74
    ramp.color_ramp.elements[1].color = (0.46, 0.18, 0.055, 1.0)
    ramp.color_ramp.elements.new(0.47).color = (0.80, 0.52, 0.23, 1.0)
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.16
    bump.inputs["Distance"].default_value = 0.00045
    links.new(texcoord.outputs["Generated"], mapping.inputs["Vector"])
    links.new(mapping.outputs["Vector"], voronoi.inputs["Vector"])
    links.new(mapping.outputs["Vector"], noise.inputs["Vector"])
    links.new(voronoi.outputs["Distance"], mix.inputs[1])
    links.new(noise.outputs["Fac"], mix.inputs[2])
    links.new(mix.outputs["Color"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return value


def textured_material(name: str, base: tuple[float, float, float, float], roughness: float, scale: float, bump_strength: float) -> bpy.types.Material:
    value = material(name, base, roughness)
    nodes = value.node_tree.nodes
    links = value.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    noise = nodes.get(name + "_NOISE") or nodes.new("ShaderNodeTexNoise")
    noise.name = name + "_NOISE"
    noise.inputs["Scale"].default_value = scale
    noise.inputs["Detail"].default_value = 5.0
    noise.inputs["Roughness"].default_value = 0.72
    bump = nodes.get(name + "_BUMP") or nodes.new("ShaderNodeBump")
    bump.name = name + "_BUMP"
    bump.inputs["Strength"].default_value = bump_strength
    bump.inputs["Distance"].default_value = 0.00055
    if not any(link.to_node == bump for link in links):
        links.new(noise.outputs["Fac"], bump.inputs["Height"])
    if not any(link.to_node == bsdf and link.to_socket == bsdf.inputs["Normal"] for link in links):
        links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return value


def make_shell(
    body: bpy.types.Object,
    name: str,
    keep,
    target: bpy.types.Collection,
    mat: bpy.types.Material,
    offset: float,
    thickness: float,
) -> bpy.types.Object:
    shell = body.copy()
    shell.data = body.data.copy()
    shell.name = name
    target.objects.link(shell)
    for modifier in tuple(shell.modifiers):
        shell.modifiers.remove(modifier)
    bm = bmesh.new()
    bm.from_mesh(shell.data)
    matrix = shell.matrix_world
    delete = [vertex for vertex in bm.verts if not keep(matrix @ vertex.co)]
    bmesh.ops.delete(bm, geom=delete, context="VERTS")
    bm.to_mesh(shell.data)
    bm.free()
    shell.data.update()
    shell.data.materials.clear()
    shell.data.materials.append(mat)
    displace = shell.modifiers.new(name + "_FIT_OFFSET", "DISPLACE")
    displace.mid_level = 0.5
    displace.strength = offset
    solidify = shell.modifiers.new(name + "_THICKNESS", "SOLIDIFY")
    solidify.thickness = thickness
    solidify.offset = 0.15
    smooth = shell.modifiers.new(name + "_SMOOTH", "SMOOTH")
    smooth.factor = 0.12
    smooth.iterations = 2
    armature = shell.modifiers.new(name + "_ARMATURE", "ARMATURE")
    armature.object = bpy.data.objects["V239_CLEAN_CHARACTER_RIG"]
    armature.use_deform_preserve_volume = True
    for polygon in shell.data.polygons:
        polygon.use_smooth = True
    shell["v241_body_derived"] = True
    shell["v241_source_body"] = body.name
    return shell


def point_at(obj: bpy.types.Object, target: Vector) -> None:
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def main() -> None:
    if Path(bpy.data.filepath).resolve() != SOURCE.resolve():
        raise RuntimeError(f"Open V240 first: {SOURCE}")
    STAGE.mkdir(parents=True, exist_ok=True)
    RENDERS.mkdir(parents=True, exist_ok=True)
    AUDIT.mkdir(parents=True, exist_ok=True)
    body = bpy.data.objects["V211_BODY_NEUTRAL"]
    target = ensure_collection("V241_RIGGED_WARDROBE")
    shirt_mat = floral_material()
    jacket_mat = textured_material("MAT_V241_CHARCOAL_JACKET", (0.018, 0.020, 0.024, 1.0), 0.48, 95.0, 0.12)
    trouser_mat = textured_material("MAT_V241_TROUSERS", (0.035, 0.031, 0.030, 1.0), 0.62, 120.0, 0.08)
    boot_mat = textured_material("MAT_V241_BOOTS", (0.115, 0.028, 0.012, 1.0), 0.32, 18.0, 0.18)

    shirt = make_shell(
        body,
        "V241_FLORAL_SHIRT",
        lambda point: 0.89 <= point.z <= 1.475
        and not (abs(point.x) > 0.285 and point.z < 1.205),
        target,
        shirt_mat,
        0.006,
        0.0032,
    )
    jacket = make_shell(
        body,
        "V241_OPEN_JACKET",
        lambda point: 0.875 <= point.z <= 1.455
        and not (abs(point.x) > 0.285 and point.z < 1.205)
        and not (point.y < -0.035 and abs(point.x) < (0.072 + max(0.0, point.z - 0.95) * 0.11)),
        target,
        jacket_mat,
        0.016,
        0.006,
    )
    trousers = make_shell(
        body,
        "V241_TROUSERS",
        # In the downward A-pose the fingertips enter the trouser z band.
        # Constrain the shell to the central lower-body envelope so hand
        # vertices can never be copied into trousers and later follow fingers.
        lambda point: 0.16 <= point.z <= 0.955 and abs(point.x) < 0.285,
        target,
        trouser_mat,
        0.010,
        0.0045,
    )
    boots = make_shell(
        body,
        "V241_BOOT_SHELLS",
        lambda point: point.z <= 0.255,
        target,
        boot_mat,
        0.018,
        0.007,
    )
    bpy.context.view_layer.update()

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.look = "AgX - Medium High Contrast"
    camera = bpy.data.objects["CAM_V211_FRONT"]
    camera.data.type = "PERSP"
    views = {
        "front": (Vector((0.0, -3.75, 1.00)), Vector((0.0, 0.0, 0.98)), 66.0),
        "three_quarter": (Vector((-2.65, -2.75, 1.10)), Vector((0.0, 0.0, 1.00)), 70.0),
        "upper": (Vector((0.0, -2.05, 1.30)), Vector((0.0, 0.0, 1.26)), 76.0),
    }
    render_records = {}
    for label, (location, look, lens) in views.items():
        camera.location = location
        camera.data.lens = lens
        point_at(camera, look)
        scene.camera = camera
        scene.render.resolution_x = 900
        scene.render.resolution_y = 1000
        scene.render.resolution_percentage = 100
        path = RENDERS / f"v241_{label}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        render_records[label] = {"path": str(path.relative_to(ROOT)), "sha256": sha256(path)}

    objects = [shirt, jacket, trousers, boots]
    scene["V241_STATUS"] = "RIGGED_BODY_DERIVED_WARDROBE_FOUNDATION"
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v241-rigged-wardrobe-foundation-v1",
        "status": "BUILT_VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha256(SOURCE)},
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha256(OUTPUT)},
        "objects": {
            obj.name: {"vertices": len(obj.data.vertices), "polygons": len(obj.data.polygons)}
            for obj in objects
        },
        "renders": render_records,
    }
    (AUDIT / "v241_manifest.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("V241_WARDROBE_FOUNDATION_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
