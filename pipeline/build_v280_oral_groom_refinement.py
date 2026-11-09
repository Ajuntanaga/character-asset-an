"""Add a driven oral cavity proof and physically based hair shading."""

from pathlib import Path
import hashlib
import json
import math

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v279_facs_body_integration" / "Character_An_facs_body_integration_v279.blend"
STAGE = ROOT / "production_v280_oral_groom_refinement"
OUTPUT = STAGE / "Character_An_oral_groom_refinement_v280.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"
HEAD = "V216_REFERENCE_FITTED_HEAD"
RIG = "V239_CLEAN_CHARACTER_RIG"


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            digest.update(block)
    return digest.hexdigest()


def point_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def material(name, color, roughness=0.5, metallic=0.0):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1.0)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1.0)
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Metallic"].default_value = metallic
    return mat


def parent_to_head(obj, rig):
    world = obj.matrix_world.copy()
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = "head"
    obj.matrix_world = world


def driver(socket, keys, expression):
    curve = socket.driver_add("default_value") if hasattr(socket, "default_value") else socket.driver_add("value")
    variable = curve.driver.variables.new()
    variable.name = "j"
    variable.type = "SINGLE_PROP"
    variable.targets[0].id_type = "KEY"
    variable.targets[0].id = keys
    variable.targets[0].data_path = 'key_blocks["jawOpen"].value'
    curve.driver.expression = expression


def transform_driver(obj, path, index, keys, expression):
    curve = obj.driver_add(path, index)
    variable = curve.driver.variables.new()
    variable.name = "j"
    variable.type = "SINGLE_PROP"
    variable.targets[0].id_type = "KEY"
    variable.targets[0].id = keys
    variable.targets[0].data_path = 'key_blocks["jawOpen"].value'
    curve.driver.expression = expression


def create_oval(name, location, radius_x, radius_z, mat, vertices=64):
    verts = [(radius_x * math.cos(2 * math.pi * i / vertices), 0.0, radius_z * math.sin(2 * math.pi * i / vertices)) for i in range(vertices)]
    mesh = bpy.data.meshes.new(name + "_MESH")
    mesh.from_pydata(verts, [], [tuple(range(vertices))])
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = location
    return obj


def create_oral_stack(head, rig):
    keys = head.data.shape_keys
    cavity = create_oval("V280_DRIVEN_ORAL_CAVITY", (0.0, -0.1545, 1.596), 0.041, 0.042, material("V280_ORAL_DARK", (0.055, 0.005, 0.008), 0.68))
    parent_to_head(cavity, rig)
    cavity.scale.z = 0.01
    transform_driver(cavity, "scale", 2, keys, "0.01 + 0.99*j")

    upper = create_oval("V280_UPPER_TEETH", (0.0, -0.1552, 1.615), 0.033, 0.008, material("V280_TEETH", (0.72, 0.61, 0.48), 0.35))
    lower = create_oval("V280_LOWER_TEETH", (0.0, -0.1553, 1.577), 0.030, 0.0065, bpy.data.materials["V280_TEETH"])
    tongue = create_oval("V280_TONGUE", (0.0, -0.1555, 1.568), 0.030, 0.010, material("V280_TONGUE_MAT", (0.28, 0.035, 0.040), 0.58))
    for obj in (upper, lower, tongue):
        parent_to_head(obj, rig)
        obj.scale.z = 0.01
        transform_driver(obj, "scale", 2, keys, "0.01 + 0.99*j")
    transform_driver(lower, "location", 2, keys, "1.577 - 0.010*j")
    transform_driver(tongue, "location", 2, keys, "1.568 - 0.006*j")
    return [cavity.name, upper.name, lower.name, tongue.name]


def refine_hair():
    hair = bpy.data.objects["V217_TIGHT_CURL_GROOM"]
    mat = hair.data.materials[0]
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    output = next(node for node in nodes if node.type == "OUTPUT_MATERIAL")
    for link in list(output.inputs["Surface"].links):
        links.remove(link)
    shader = nodes.get("V280_PRINCIPLED_HAIR") or nodes.new("ShaderNodeBsdfHairPrincipled")
    shader.name = "V280_PRINCIPLED_HAIR"
    shader.parametrization = "MELANIN"
    values = {
        "Melanin": 0.82,
        "Melanin Redness": 0.22,
        "Roughness": 0.46,
        "Radial Roughness": 0.34,
        "Coat": 0.08,
        "IOR": 1.45,
        "Random Roughness": 0.12,
        "Random": 0.08,
    }
    for name, value in values.items():
        if name in shader.inputs:
            shader.inputs[name].default_value = value
    links.new(shader.outputs[0], output.inputs["Surface"])
    hair.data.bevel_depth = 0.00032
    return {"object": hair.name, "shader": shader.bl_idname, "bevel_depth_m": hair.data.bevel_depth, "parameters": values}


def clear(keys):
    for key in keys[1:]:
        key.value = 0.0
    bpy.context.view_layer.update()


def render(scene, camera, path):
    scene.camera = camera
    scene.render.resolution_x = 768
    scene.render.resolution_y = 768
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(path)}


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    for folder in (STAGE, RENDERS, AUDIT):
        folder.mkdir(parents=True, exist_ok=True)
    head = bpy.data.objects[HEAD]
    rig = bpy.data.objects[RIG]
    oral_objects = create_oral_stack(head, rig)
    hair_record = refine_hair()
    scene = bpy.context.scene
    camera = bpy.data.objects["V279_PORTRAIT_CAMERA"]
    camera.location = Vector((0.0, -1.50, 1.66))
    point_at(camera, Vector((0.0, -0.025, 1.64)))
    keys = head.data.shape_keys.key_blocks
    clear(keys)
    renders = {"neutral": render(scene, camera, RENDERS / "v280_neutral.png")}
    keys["jawOpen"].value = 0.72
    bpy.context.view_layer.update()
    renders["jaw_open"] = render(scene, camera, RENDERS / "v280_jaw_open.png")
    clear(keys)
    keys["mouthSmileLeft"].value = 0.92
    keys["mouthSmileRight"].value = 0.92
    bpy.context.view_layer.update()
    renders["smile"] = render(scene, camera, RENDERS / "v280_smile.png")
    clear(keys)
    bpy.context.view_layer.update()
    scene["V280_STATUS"] = "ORAL_GROOM_REFINEMENT_VISUAL_REVIEW_REQUIRED"
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v280-oral-groom-refinement-v1",
        "status": "BUILT_VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)},
        "oral_objects": oral_objects,
        "hair": hair_record,
        "renders": renders,
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha(OUTPUT)},
    }
    (AUDIT / "v280_oral_groom_refinement.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V280_ORAL_GROOM_REFINEMENT_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
