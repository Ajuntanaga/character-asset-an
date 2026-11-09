"""Tailor V283 wardrobe proportions and add clean garment/boot construction details."""

from pathlib import Path
import hashlib
import json

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v283_anatomical_wardrobe" / "Character_An_anatomical_wardrobe_v283.blend"
STAGE = ROOT / "production_v284_wardrobe_tailoring"
OUTPUT = STAGE / "Character_An_wardrobe_tailoring_v284.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"
RIG = "V239_CLEAN_CHARACTER_RIG"


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            digest.update(block)
    return digest.hexdigest()


def point_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def material(name, dark, light, roughness, scale):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = roughness
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = scale
    noise.inputs["Detail"].default_value = 4.0
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*dark, 1.0)
    ramp.color_ramp.elements[1].color = (*light, 1.0)
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.10
    bump.inputs["Distance"].default_value = 0.0006
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def add_smooth_first(obj, factor, iterations):
    modifier = obj.modifiers.new("V284_RELAX_TAILORING", "SMOOTH")
    modifier.factor = factor
    modifier.iterations = iterations
    obj.modifiers.move(len(obj.modifiers) - 1, 0)


def curve_detail(name, points, bevel, material_value):
    curve_data = bpy.data.curves.new(name + "_CURVE", "CURVE")
    curve_data.dimensions = "3D"
    curve_data.bevel_depth = bevel
    curve_data.bevel_resolution = 3
    spline = curve_data.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for point, coordinate in zip(spline.bezier_points, points):
        point.co = coordinate
        point.handle_left_type = "AUTO"
        point.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(name, curve_data)
    bpy.context.scene.collection.objects.link(obj)
    curve_data.materials.append(material_value)
    return obj


def add_toe_cap(name, location, material_value):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, location=location)
    obj = bpy.context.view_layer.objects.active
    obj.name = name
    obj.scale = (0.082, 0.118, 0.052)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material_value)
    return obj


def parent_bone(obj, rig, bone):
    world = obj.matrix_world.copy()
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = bone
    obj.matrix_world = world


def render(scene, camera, path):
    scene.camera = camera
    scene.render.resolution_x = 768
    scene.render.resolution_y = 1024
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(path)}


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    for folder in (STAGE, RENDERS, AUDIT):
        folder.mkdir(parents=True, exist_ok=True)
    rig = bpy.data.objects[RIG]
    jacket = bpy.data.objects["V283_FITTED_DENIM_JACKET"]
    shirt = bpy.data.objects["V283_TAILORED_SHIRT"]
    trousers = bpy.data.objects["V283_TAILORED_TROUSERS"]
    boots = bpy.data.objects["V283_CHELSEA_BOOT_UPPERS"]

    denim = material("V284_SMOKED_INDIGO_DENIM", (0.010, 0.016, 0.024), (0.055, 0.080, 0.110), 0.70, 135.0)
    floral = material("V284_OXBLOOD_FLORAL", (0.035, 0.004, 0.008), (0.42, 0.075, 0.025), 0.60, 13.0)
    trouser_mat = material("V284_BLACK_WOOL", (0.006, 0.007, 0.009), (0.028, 0.032, 0.040), 0.77, 120.0)
    leather = material("V284_CHESTNUT_LEATHER", (0.025, 0.006, 0.002), (0.16, 0.035, 0.008), 0.38, 28.0)
    trim = material("V284_DENIM_SEAM", (0.030, 0.043, 0.058), (0.10, 0.13, 0.16), 0.68, 80.0)
    jacket.data.materials.clear(); jacket.data.materials.append(denim)
    shirt.data.materials.clear(); shirt.data.materials.append(floral)
    trousers.data.materials.clear(); trousers.data.materials.append(trouser_mat)
    boots.data.materials.clear(); boots.data.materials.append(leather)

    add_smooth_first(jacket, 0.42, 4)
    add_smooth_first(shirt, 0.26, 3)
    add_smooth_first(trousers, 0.22, 3)
    add_smooth_first(boots, 0.34, 4)

    # Relax the trousers away from the anatomy so they read as cloth, not leggings.
    for vertex in trousers.data.vertices:
        x_axis = 0.093 if vertex.co.x >= 0 else -0.093
        vertex.co.x = x_axis + (vertex.co.x - x_axis) * 1.07
        vertex.co.y = 0.005 + (vertex.co.y - 0.005) * 1.055

    # Clean front construction lines obscure the polygon-step extraction edge.
    details = [
        curve_detail("V284_JACKET_EDGE_L", [(-.054, -.157, 1.015), (-.060, -.167, 1.26), (-.073, -.150, 1.48)], .008, trim),
        curve_detail("V284_JACKET_EDGE_R", [(.054, -.157, 1.015), (.060, -.167, 1.26), (.073, -.150, 1.48)], .008, trim),
        curve_detail("V284_JACKET_HEM", [(-.255, -.040, .995), (0.0, -.145, .988), (.255, -.040, .995)], .007, trim),
        curve_detail("V284_SHIRT_PLACKET", [(0.0, -.151, 1.00), (0.0, -.160, 1.25), (0.0, -.145, 1.45)], .004, floral),
    ]
    for obj in details:
        obj.parent = rig

    caps = []
    for side, x, bone in (("L", .093, "foot_fk.L"), ("R", -.093, "foot_fk.R")):
        cap = add_toe_cap(f"V284_BOOT_TOE_CAP_{side}", (x, -.135, .070), leather)
        parent_bone(cap, rig, bone)
        caps.append(cap)

    scene = bpy.context.scene
    camera = bpy.data.objects.get("V283_FULL_CAMERA")
    camera.name = "V284_FULL_CAMERA"
    camera.location = Vector((0.0, -5.25, 1.00))
    point_at(camera, Vector((0.0, 0.0, .93)))
    renders = {"front": render(scene, camera, RENDERS / "v284_tailored_front.png")}
    camera.location = Vector((-3.0, -4.25, 1.12))
    point_at(camera, Vector((0.0, 0.0, .98)))
    renders["three_quarter"] = render(scene, camera, RENDERS / "v284_tailored_three_quarter.png")
    scene["V284_STATUS"] = "TAILORED_WARDROBE_VISUAL_REVIEW_REQUIRED"
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v284-wardrobe-tailoring-v1",
        "status": "BUILT_VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)},
        "details": [obj.name for obj in details],
        "toe_caps": [obj.name for obj in caps],
        "renders": renders,
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha(OUTPUT)},
    }
    (AUDIT / "v284_wardrobe_tailoring.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V284_WARDROBE_TAILORING_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
