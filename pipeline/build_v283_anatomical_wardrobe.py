"""Build anatomical, rig-weighted wardrobe shells from the clean body surface."""

from pathlib import Path
import hashlib
import json

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v281_dynamic_oral_shader" / "Character_An_dynamic_oral_shader_v281.blend"
STAGE = ROOT / "production_v283_anatomical_wardrobe"
OUTPUT = STAGE / "Character_An_anatomical_wardrobe_v283.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"
BODY = "V211_BODY_NEUTRAL"
RIG = "V239_CLEAN_CHARACTER_RIG"


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            digest.update(block)
    return digest.hexdigest()


def point_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def fabric(name, dark, light, roughness=0.72, scale=90.0, metallic=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = scale
    noise.inputs["Detail"].default_value = 3.0
    noise.inputs["Roughness"].default_value = 0.72
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*dark, 1.0)
    ramp.color_ramp.elements[1].color = (*light, 1.0)
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.16
    bump.inputs["Distance"].default_value = 0.0007
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def vertex_weight_maps(body):
    names = {group.index: group.name for group in body.vertex_groups}
    maps = []
    for vertex in body.data.vertices:
        maps.append({names[item.group]: item.weight for item in vertex.groups if item.group in names})
    return maps


def influence(weight_map, fragments):
    return sum(weight for name, weight in weight_map.items() if any(fragment in name for fragment in fragments))


def extract_shell(name, body, rig, material, selector, offset, thickness):
    source = body.data
    weight_maps = vertex_weight_maps(body)
    selected = []
    for polygon in source.polygons:
        center = sum((source.vertices[index].co for index in polygon.vertices), Vector()) / len(polygon.vertices)
        aggregate = {}
        for index in polygon.vertices:
            for group_name, weight in weight_maps[index].items():
                aggregate[group_name] = aggregate.get(group_name, 0.0) + weight / len(polygon.vertices)
        if selector(center, aggregate):
            selected.append(polygon)
    used = sorted({index for polygon in selected for index in polygon.vertices})
    remap = {old: new for new, old in enumerate(used)}
    vertices = [source.vertices[index].co + source.vertices[index].normal * offset for index in used]
    faces = [[remap[index] for index in polygon.vertices] for polygon in selected]
    mesh = bpy.data.meshes.new(name + "_MESH")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    mesh.materials.append(material)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.matrix_world = body.matrix_world.copy()
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    for source_group in body.vertex_groups:
        target_group = obj.vertex_groups.new(name=source_group.name)
        assignments = []
        for new_index, old_index in enumerate(used):
            weight = weight_maps[old_index].get(source_group.name)
            if weight is not None:
                assignments.append((new_index, weight))
        for vertex_index, weight in assignments:
            target_group.add([vertex_index], weight, "REPLACE")
    solid = obj.modifiers.new("V283_CLOTH_THICKNESS", "SOLIDIFY")
    solid.thickness = thickness
    solid.offset = 0.0
    bevel = obj.modifiers.new("V283_SOFT_HEMS", "BEVEL")
    bevel.width = min(thickness * 0.6, 0.003)
    bevel.segments = 2
    armature = obj.modifiers.new("V283_RIG", "ARMATURE")
    armature.object = rig
    return obj, len(selected)


def add_sole(name, location, scale, material):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.view_layer.objects.active
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    bevel = obj.modifiers.new("V283_SOLE_ROUNDING", "BEVEL")
    bevel.width = 0.015
    bevel.segments = 4
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
    body, rig = bpy.data.objects[BODY], bpy.data.objects[RIG]
    denim = fabric("V283_WASHED_BLACK_DENIM", (0.012, 0.016, 0.021), (0.052, 0.064, 0.078), 0.69, 125.0)
    shirt_mat = fabric("V283_BURNT_FLORAL_SHIRT", (0.09, 0.026, 0.012), (0.48, 0.19, 0.035), 0.61, 18.0)
    trouser_mat = fabric("V283_CHARCOAL_TROUSERS", (0.010, 0.012, 0.015), (0.035, 0.040, 0.048), 0.74, 105.0)
    leather = fabric("V283_DARK_CHESTNUT_LEATHER", (0.035, 0.010, 0.004), (0.19, 0.052, 0.012), 0.42, 23.0)
    sole_mat = fabric("V283_BOOT_SOLE", (0.006, 0.004, 0.003), (0.018, 0.012, 0.009), 0.82, 75.0)

    torso_groups = ("DEF-spine", "DEF-breast")
    arm_groups = ("DEF-shoulder", "DEF-upper_arm", "DEF-forearm")
    leg_groups = ("DEF-pelvis", "DEF-thigh", "DEF-shin")
    foot_groups = ("DEF-foot", "DEF-toe")

    def shirt_selector(center, weights):
        return 0.98 <= center.z <= 1.50 and abs(center.x) < 0.265 and influence(weights, torso_groups) > 0.18

    def jacket_selector(center, weights):
        torso = 0.97 <= center.z <= 1.51 and abs(center.x) < 0.285 and influence(weights, torso_groups) > 0.12
        sleeves = influence(weights, arm_groups) > 0.22 and influence(weights, ("DEF-hand",)) < 0.12
        front_opening = center.y < -0.055 and abs(center.x) < 0.050 and center.z > 1.02
        return (torso or sleeves) and not front_opening

    def trousers_selector(center, weights):
        return 0.105 <= center.z <= 1.01 and influence(weights, leg_groups) > 0.16

    def boots_selector(center, weights):
        return center.z <= 0.235 and (influence(weights, foot_groups) > 0.12 or influence(weights, ("DEF-shin",)) > 0.20)

    garments = {}
    garments["shirt"], shirt_faces = extract_shell("V283_TAILORED_SHIRT", body, rig, shirt_mat, shirt_selector, 0.007, 0.003)
    garments["jacket"], jacket_faces = extract_shell("V283_FITTED_DENIM_JACKET", body, rig, denim, jacket_selector, 0.018, 0.006)
    garments["trousers"], trouser_faces = extract_shell("V283_TAILORED_TROUSERS", body, rig, trouser_mat, trousers_selector, 0.012, 0.004)
    garments["boots"], boot_faces = extract_shell("V283_CHELSEA_BOOT_UPPERS", body, rig, leather, boots_selector, 0.021, 0.007)

    soles = []
    for side, x, bone in (("L", .093, "foot_fk.L"), ("R", -.093, "foot_fk.R")):
        sole = add_sole(f"V283_BOOT_SOLE_{side}", (x, -0.055, 0.023), (0.078, 0.145, 0.018), sole_mat)
        parent_bone(sole, rig, bone)
        soles.append(sole)

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    camera_data = bpy.data.cameras.new("V283_FULL_CAMERA_DATA")
    camera = bpy.data.objects.new("V283_FULL_CAMERA", camera_data)
    scene.collection.objects.link(camera)
    camera.data.lens = 72.0
    camera.location = Vector((0.0, -5.25, 1.00))
    point_at(camera, Vector((0.0, 0.0, .93)))
    renders = {"front": render(scene, camera, RENDERS / "v283_wardrobe_front.png")}
    camera.location = Vector((-3.0, -4.25, 1.12))
    point_at(camera, Vector((0.0, 0.0, .98)))
    renders["three_quarter"] = render(scene, camera, RENDERS / "v283_wardrobe_three_quarter.png")
    scene["V283_STATUS"] = "ANATOMICAL_WARDROBE_VISUAL_REVIEW_REQUIRED"
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v283-anatomical-wardrobe-v1",
        "status": "BUILT_VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)},
        "garments": {key: value.name for key, value in garments.items()},
        "selected_faces": {"shirt": shirt_faces, "jacket": jacket_faces, "trousers": trouser_faces, "boots": boot_faces},
        "renders": renders,
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha(OUTPUT)},
    }
    (AUDIT / "v283_anatomical_wardrobe.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V283_ANATOMICAL_WARDROBE_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
