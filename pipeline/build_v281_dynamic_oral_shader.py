"""Mask the FaceBuilder jaw-open texture stretch with a driven oral shader."""

from pathlib import Path
import hashlib
import json
import math

import bpy


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v280_oral_groom_refinement" / "Character_An_oral_groom_refinement_v280.blend"
STAGE = ROOT / "production_v281_dynamic_oral_shader"
OUTPUT = STAGE / "Character_An_dynamic_oral_shader_v281.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"
HEAD = "V216_REFERENCE_FITTED_HEAD"


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            digest.update(block)
    return digest.hexdigest()


def clear(keys):
    for key in keys[1:]:
        key.value = 0.0
    bpy.context.view_layer.update()


def install_mask(head):
    mesh = head.data
    attr = mesh.color_attributes.get("V281_ORAL_MASK")
    if attr:
        mesh.color_attributes.remove(attr)
    attr = mesh.color_attributes.new(name="V281_ORAL_MASK", type="FLOAT_COLOR", domain="POINT")
    matrix = head.matrix_world
    weights = []
    for vertex in mesh.vertices:
        world = matrix @ vertex.co
        dx = world.x / 0.041
        dz = (world.z - 1.588) / 0.037
        radial = math.exp(-3.0 * (dx * dx + dz * dz))
        front = min(1.0, max(0.0, (-0.105 - world.y) / 0.043))
        weight = radial * front
        weights.append(weight)
        attr.data[vertex.index].color = (weight, weight, weight, 1.0)

    material = head.data.materials[0]
    material.use_nodes = True
    tree = material.node_tree
    shader = next(node for node in tree.nodes if node.type == "BSDF_PRINCIPLED")
    base = shader.inputs["Base Color"]
    if not base.is_linked:
        raise RuntimeError("Expected the FaceBuilder image texture to drive Base Color")
    original = base.links[0].from_socket
    tree.links.remove(base.links[0])
    attribute = tree.nodes.new("ShaderNodeVertexColor")
    attribute.name = "V281_ORAL_VERTEX_MASK"
    attribute.layer_name = "V281_ORAL_MASK"
    strength = tree.nodes.new("ShaderNodeValue")
    strength.name = "V281_JAW_OPEN_STRENGTH"
    strength.outputs[0].default_value = 0.0
    curve = strength.outputs[0].driver_add("default_value")
    variable = curve.driver.variables.new()
    variable.name = "j"
    variable.type = "SINGLE_PROP"
    variable.targets[0].id_type = "KEY"
    variable.targets[0].id = mesh.shape_keys
    variable.targets[0].data_path = 'key_blocks["jawOpen"].value'
    curve.driver.expression = "min(1.0, j * 1.35)"
    multiply = tree.nodes.new("ShaderNodeMath")
    multiply.name = "V281_ORAL_MASK_X_JAW"
    multiply.operation = "MULTIPLY"
    mix = tree.nodes.new("ShaderNodeMixRGB")
    mix.name = "V281_DYNAMIC_ORAL_COLOR"
    mix.blend_type = "MIX"
    mix.inputs[2].default_value = (0.035, 0.0015, 0.0025, 1.0)
    tree.links.new(attribute.outputs["Color"], multiply.inputs[0])
    tree.links.new(strength.outputs[0], multiply.inputs[1])
    tree.links.new(multiply.outputs[0], mix.inputs[0])
    tree.links.new(original, mix.inputs[1])
    tree.links.new(mix.outputs[0], base)
    return {
        "attribute": attr.name,
        "nonzero_vertices": sum(weight > 0.01 for weight in weights),
        "max_weight": max(weights),
        "material": material.name,
    }


def render(scene, path):
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(path)}


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    for folder in (STAGE, RENDERS, AUDIT):
        folder.mkdir(parents=True, exist_ok=True)
    head = bpy.data.objects[HEAD]
    mask_record = install_mask(head)
    scene = bpy.context.scene
    scene.camera = bpy.data.objects["V279_PORTRAIT_CAMERA"]
    scene.render.resolution_x = 768
    scene.render.resolution_y = 768
    keys = head.data.shape_keys.key_blocks
    clear(keys)
    neutral = render(scene, RENDERS / "v281_neutral.png")
    keys["jawOpen"].value = 0.72
    bpy.context.view_layer.update()
    jaw = render(scene, RENDERS / "v281_jaw_open.png")
    clear(keys)
    scene["V281_STATUS"] = "DYNAMIC_ORAL_SHADER_VISUAL_REVIEW_REQUIRED"
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v281-dynamic-oral-shader-v1",
        "status": "BUILT_VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)},
        "mask": mask_record,
        "renders": {"neutral": neutral, "jaw_open": jaw},
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha(OUTPUT)},
    }
    (AUDIT / "v281_dynamic_oral_shader.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V281_DYNAMIC_ORAL_SHADER_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
