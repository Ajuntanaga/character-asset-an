"""Build a deformable wardrobe foundation from the corrected male topology."""

from pathlib import Path
import hashlib
import json
import math

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v324_identity_cleanup" / "Character_An_identity_cleanup_v324.blend"
STAGE = ROOT / "production_v325_wardrobe_foundation"
OUTPUT = STAGE / "Character_An_wardrobe_foundation_v325.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit" / "v325_wardrobe_foundation.json"
FLORAL = ROOT / "textures" / "wardrobe" / "dark_floral_shirt_basecolor_v1.png"
BODY = "V322_MB_MALE_BODY"
RIG = "V322_MB_MALE_RIG"


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            digest.update(block)
    return digest.hexdigest()


def aim(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(scene, camera, path, location, target, lens, resolution):
    camera.location = location
    camera.data.lens = lens
    aim(camera, target)
    scene.camera = camera
    scene.render.resolution_x, scene.render.resolution_y = resolution
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(path)}


def principled(material):
    return material.node_tree.nodes.get("Principled BSDF")


def make_floral_material():
    material = bpy.data.materials.new("V325_DARK_FLORAL_COTTON")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    bsdf = principled(material)
    bsdf.inputs["Roughness"].default_value = 0.63
    bsdf.inputs["Specular IOR Level"].default_value = 0.24
    image_node = nodes.new("ShaderNodeTexImage")
    image_node.name = "V325_FLORAL_BASECOLOR"
    image_node.image = bpy.data.images.load(str(FLORAL), check_existing=True)
    image_node.extension = "REPEAT"
    image_node.projection = "BOX"
    image_node.projection_blend = 0.18
    texcoord = nodes.new("ShaderNodeTexCoord")
    mapping = nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (3.35, 3.35, 3.35)
    grade = nodes.new("ShaderNodeHueSaturation")
    grade.inputs["Saturation"].default_value = 0.78
    grade.inputs["Value"].default_value = 0.48
    links.new(texcoord.outputs["Generated"], mapping.inputs["Vector"])
    links.new(mapping.outputs["Vector"], image_node.inputs["Vector"])
    links.new(image_node.outputs["Color"], grade.inputs["Color"])
    links.new(grade.outputs["Color"], bsdf.inputs["Base Color"])
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.12
    bump.inputs["Distance"].default_value = 0.00055
    links.new(image_node.outputs["Color"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return material


def make_denim_material(name, base_a, base_b, roughness):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    bsdf = principled(material)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Specular IOR Level"].default_value = 0.20
    texcoord = nodes.new("ShaderNodeTexCoord")
    mapping = nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (1.0, 1.0, 1.0)
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 165.0
    noise.inputs["Detail"].default_value = 2.2
    noise.inputs["Roughness"].default_value = 0.72
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.22
    ramp.color_ramp.elements[0].color = (*base_a, 1.0)
    ramp.color_ramp.elements[1].position = 0.78
    ramp.color_ramp.elements[1].color = (*base_b, 1.0)
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.16
    bump.inputs["Distance"].default_value = 0.0004
    links.new(texcoord.outputs["Object"], mapping.inputs["Vector"])
    links.new(mapping.outputs["Vector"], noise.inputs["Vector"])
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return material


def make_simple_material(name, color, roughness=0.48, metallic=0.0):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    bsdf = principled(material)
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return material


def extract_shell(source, rig, name, predicate, offset, thickness, material, material_indices=(0,)):
    selected = []
    used = set()
    for polygon in source.data.polygons:
        if polygon.material_index not in material_indices:
            continue
        world_center = source.matrix_world @ polygon.center
        if not predicate(world_center):
            continue
        selected.append(polygon)
        used.update(polygon.vertices)
    old_indices = sorted(used)
    remap = {old: new for new, old in enumerate(old_indices)}
    vertices = []
    for old in old_indices:
        vertex = source.data.vertices[old]
        vertices.append(vertex.co + vertex.normal * offset)
    faces = [[remap[index] for index in polygon.vertices] for polygon in selected]
    mesh = bpy.data.meshes.new(name + "_MESH")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.matrix_world = source.matrix_world.copy()
    obj.data.materials.append(material)
    for source_group in source.vertex_groups:
        obj.vertex_groups.new(name=source_group.name)
    for old, new in remap.items():
        for membership in source.data.vertices[old].groups:
            obj.vertex_groups[membership.group].add([new], membership.weight, "REPLACE")
    armature = obj.modifiers.new("V325_ARMATURE", "ARMATURE")
    armature.object = rig
    subdivision = obj.modifiers.new("V325_SURFACE_SUBDIVISION", "SUBSURF")
    subdivision.levels = 1
    subdivision.render_levels = 1
    solidify = obj.modifiers.new("V325_CLOTH_THICKNESS", "SOLIDIFY")
    solidify.thickness = thickness
    solidify.offset = 0.0
    solidify.use_rim = True
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    return obj, {
        "polygons": len(selected),
        "vertices": len(old_indices),
        "offset_m": offset,
        "thickness_m": thickness,
    }


def add_panel(name, points, material, thickness=0.003):
    mesh = bpy.data.meshes.new(name + "_MESH")
    mesh.from_pydata(points, [], [list(range(len(points)))])
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(material)
    solidify = obj.modifiers.new("V325_PANEL_THICKNESS", "SOLIDIFY")
    solidify.thickness = thickness
    solidify.offset = 0.0
    bevel = obj.modifiers.new("V325_PANEL_EDGE", "BEVEL")
    bevel.width = 0.0012
    bevel.segments = 2
    return obj


def add_curve(name, points, material, bevel_depth=0.0013, cyclic=False):
    curve = bpy.data.curves.new(name + "_CURVE", "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 2
    curve.bevel_depth = bevel_depth
    curve.bevel_resolution = 2
    spline = curve.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for point, co in zip(spline.points, points):
        point.co = (*co, 1.0)
    spline.use_cyclic_u = cyclic
    obj = bpy.data.objects.new(name, curve)
    bpy.context.scene.collection.objects.link(obj)
    curve.materials.append(material)
    return obj


def parent_to_bone(obj, rig, bone):
    candidates = (bone, "torso", "spine_fk.003", "DEF-spine.003", "ORG-spine.003")
    resolved = next((candidate for candidate in candidates if candidate in rig.pose.bones), None)
    if resolved is None:
        raise RuntimeError(f"No torso parent bone found for {obj.name}")
    world = obj.matrix_world.copy()
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = resolved
    obj.matrix_world = world


def add_button(name, location, material, rig, radius=0.009):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=radius, location=location)
    button = bpy.context.object
    button.name = name
    button.scale.y = 0.42
    button.data.materials.append(material)
    parent_to_bone(button, rig, "chest")
    return button


def add_wardrobe_details(rig, floral, jacket, stitch, brass):
    details = []
    # Shirt collar sits high enough to conceal the provisional head/body join.
    left_collar = add_panel(
        "V325_SHIRT_COLLAR_L",
        [(-0.058, -0.098, 1.600), (-0.004, -0.123, 1.578), (-0.068, -0.137, 1.526), (-0.094, -0.107, 1.560)],
        floral,
        0.0022,
    )
    right_collar = add_panel(
        "V325_SHIRT_COLLAR_R",
        [(0.058, -0.098, 1.600), (0.004, -0.123, 1.578), (0.068, -0.137, 1.526), (0.094, -0.107, 1.560)],
        floral,
        0.0022,
    )
    details.extend((left_collar, right_collar))
    # Broad dark lapels and edge stitching reproduce the locked work-jacket hierarchy.
    left_lapel = add_panel(
        "V325_JACKET_LAPEL_L",
        [(-0.176, -0.142, 1.520), (-0.074, -0.168, 1.510), (-0.068, -0.186, 1.285), (-0.155, -0.175, 1.360)],
        jacket,
        0.004,
    )
    right_lapel = add_panel(
        "V325_JACKET_LAPEL_R",
        [(0.176, -0.142, 1.520), (0.074, -0.168, 1.510), (0.068, -0.186, 1.285), (0.155, -0.175, 1.360)],
        jacket,
        0.004,
    )
    details.extend((left_lapel, right_lapel))
    for label, sign in (("L", -1.0), ("R", 1.0)):
        pocket = add_panel(
            f"V325_CHEST_POCKET_{label}",
            [
                (sign * 0.105, -0.202, 1.333),
                (sign * 0.198, -0.181, 1.333),
                (sign * 0.190, -0.188, 1.244),
                (sign * 0.112, -0.205, 1.244),
            ],
            jacket,
            0.003,
        )
        seam = add_curve(
            f"V325_POCKET_STITCH_{label}",
            [
                Vector((sign * 0.112, -0.205, 1.327)),
                Vector((sign * 0.192, -0.184, 1.327)),
                Vector((sign * 0.185, -0.190, 1.250)),
                Vector((sign * 0.118, -0.204, 1.250)),
            ],
            stitch,
            0.00105,
            True,
        )
        details.extend((pocket, seam))
    for index, z in enumerate((1.445, 1.325, 1.195, 1.060, 0.920)):
        details.append(add_button(f"V325_JACKET_BUTTON_{index + 1}", Vector((-0.060, -0.202, z)), brass, rig, 0.0072))
    for obj in details:
        if obj.parent is None:
            parent_to_bone(obj, rig, "chest")
    return [obj.name for obj in details]


def neutralize_preview_lighting():
    settings = {
        "V323_KEY": (360.0, (1.0, 0.97, 0.94)),
        "V323_FILL": (135.0, (0.82, 0.90, 1.0)),
        "V323_RIM": (165.0, (0.66, 0.76, 1.0)),
    }
    for name, (energy, color) in settings.items():
        light = bpy.data.objects.get(name)
        if light and light.type == "LIGHT":
            light.data.energy = energy
            light.data.color = color
    groom = bpy.data.objects.get("V217_TIGHT_CURL_GROOM")
    if groom:
        for slot in groom.material_slots:
            material = slot.material
            if not material or not material.node_tree:
                continue
            for node in material.node_tree.nodes:
                if node.type == "BSDF_HAIR_PRINCIPLED":
                    if "Color" in node.inputs:
                        node.inputs["Color"].default_value = (0.00008, 0.00010, 0.00016, 1.0)
                    if "Melanin" in node.inputs:
                        node.inputs["Melanin"].default_value = 1.0
                    if "Melanin Redness" in node.inputs:
                        node.inputs["Melanin Redness"].default_value = 0.0
                    if "Absorption Coefficient" in node.inputs:
                        node.inputs["Absorption Coefficient"].default_value = (7.0, 7.0, 7.0)
    return settings


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    for folder in (STAGE, RENDERS, AUDIT.parent):
        folder.mkdir(parents=True, exist_ok=True)
    body = bpy.data.objects[BODY]
    rig = bpy.data.objects[RIG]
    floral = make_floral_material()
    jacket_material = make_denim_material("V325_BLACK_WORK_JACKET", (0.00035, 0.00045, 0.00060), (0.0040, 0.0050, 0.0065), 0.61)
    pants_material = make_denim_material("V325_BLACK_DENIM_TROUSERS", (0.00025, 0.00030, 0.00038), (0.0022, 0.0027, 0.0034), 0.67)
    stitch = make_simple_material("V325_MUTED_TAN_STITCH", (0.11, 0.072, 0.038), 0.58)
    brass = make_simple_material("V325_ANTIQUE_BRASS", (0.18, 0.075, 0.018), 0.31, 0.72)

    shirt, shirt_stats = extract_shell(
        body, rig, "V325_FLORAL_SHIRT",
        lambda co: 0.82 <= co.z <= 1.55 and abs(co.x) < 0.29,
        0.0055, 0.0022, floral,
    )
    jacket, jacket_stats = extract_shell(
        body, rig, "V325_WORK_JACKET",
        lambda co: (
            0.80 <= co.z <= 1.55
            and abs(co.x) < 0.665
            and not (co.y < -0.115 and abs(co.x) < 0.078 and co.z > 0.88)
        ),
        0.012, 0.0040, jacket_material,
    )
    pants, pants_stats = extract_shell(
        body, rig, "V325_TROUSERS",
        lambda co: 0.15 <= co.z <= 1.03,
        0.0075, 0.0035, pants_material, (0, 1),
    )
    details = add_wardrobe_details(rig, floral, jacket_material, stitch, brass)
    lights = neutralize_preview_lighting()

    scene = bpy.context.scene
    scene["V325_STATUS"] = "DEFORMABLE_WARDROBE_FOUNDATION_VISUAL_REVIEW_REQUIRED"
    camera = bpy.data.objects["V323_CAMERA"]
    renders = {
        "full_front": render(scene, camera, RENDERS / "v325_full_front.png", Vector((0.0, -3.55, 1.02)), Vector((0.0, 0.0, 1.0)), 68.0, (900, 1100)),
        "full_three_quarter": render(scene, camera, RENDERS / "v325_full_three_quarter.png", Vector((2.05, -3.05, 1.12)), Vector((0.0, 0.0, 1.0)), 70.0, (900, 1100)),
        "torso_front": render(scene, camera, RENDERS / "v325_torso_front.png", Vector((0.0, -2.05, 1.23)), Vector((0.0, -0.02, 1.20)), 82.0, (900, 1000)),
    }
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v325-wardrobe-foundation-v1",
        "status": "BUILT_VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)},
        "floral_texture": {"path": str(FLORAL.relative_to(ROOT)), "sha256": sha(FLORAL)},
        "garments": {
            shirt.name: shirt_stats,
            jacket.name: jacket_stats,
            pants.name: pants_stats,
        },
        "details": details,
        "preview_lighting": lights,
        "renders": renders,
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha(OUTPUT)},
    }
    AUDIT.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V325_WARDROBE_FOUNDATION_OK=" + json.dumps({
        "garments": record["garments"],
        "detail_count": len(details),
        "output_sha256": record["output"]["sha256"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
