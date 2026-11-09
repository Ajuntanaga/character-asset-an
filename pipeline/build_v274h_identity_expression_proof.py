"""Refine the FaceBuilder identity presentation and prove core facial poses."""

from pathlib import Path
import hashlib
import json

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v274g_facebuilder_animation_bridge" / "Character_An_facebuilder_animation_bridge_v274g.blend"
STAGE = ROOT / "production_v274h_identity_expression_proof"
OUTPUT = STAGE / "Character_An_identity_expression_proof_v274h.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"
DONOR = "V216_REFERENCE_FITTED_HEAD"
DRIVER = "V276E_GEO-head_animation_realistic"


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            digest.update(block)
    return digest.hexdigest()


def point_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def principled(material):
    if not material or not material.use_nodes:
        return None
    return next((node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED"), None)


def refine_groom():
    hair = bpy.data.objects["V217_TIGHT_CURL_GROOM"]
    hair.hide_render = False
    hair.hide_viewport = False
    # The donor groom was nearly 1 mm thick and read as silver wire. Realistic
    # tightly curled strands need a dark, finer silhouette and restrained gloss.
    hair.data.bevel_depth = 0.00028
    hair.data.bevel_resolution = 1
    hair.data.resolution_u = 1
    material = hair.data.materials[0]
    shader = principled(material)
    if shader:
        shader.inputs["Base Color"].default_value = (0.009, 0.0045, 0.0025, 1.0)
        shader.inputs["Roughness"].default_value = 0.49
        shader.inputs["Specular IOR Level"].default_value = 0.24
        if "Coat Weight" in shader.inputs:
            shader.inputs["Coat Weight"].default_value = 0.06
        if "Coat Roughness" in shader.inputs:
            shader.inputs["Coat Roughness"].default_value = 0.36
    # The baked 4K face already contains the reference beard and brows. The old
    # curve overlays create comb-like bars and floating stubble, so retire them.
    for name in ("V217_BEARD_STUBBLE", "V217_BROWS"):
        obj = bpy.data.objects[name]
        obj.hide_render = True
        obj.hide_viewport = True
    return {
        "hair_splines": len(hair.data.splines),
        "hair_bevel_depth_m": hair.data.bevel_depth,
        "curve_overlays_hidden": ["V217_BEARD_STUBBLE", "V217_BROWS"],
    }


def refine_skin():
    donor = bpy.data.objects[DONOR]
    material = donor.data.materials[0]
    shader = principled(material)
    if not shader:
        return {"material": material.name if material else None, "adjusted": False}
    shader.inputs["Roughness"].default_value = 0.60
    shader.inputs["Specular IOR Level"].default_value = 0.16
    shader.inputs["Subsurface Weight"].default_value = 0.02
    shader.inputs["Subsurface Scale"].default_value = 0.00045
    tree = material.node_tree
    base = shader.inputs["Base Color"]
    link = base.links[0] if base.is_linked else None
    if link and not tree.nodes.get("V274H_IDENTITY_GRADE"):
        source_socket = link.from_socket
        grade = tree.nodes.new("ShaderNodeHueSaturation")
        grade.name = "V274H_IDENTITY_GRADE"
        grade.label = "Reference identity grade"
        grade.inputs["Hue"].default_value = 0.49
        grade.inputs["Saturation"].default_value = 1.08
        grade.inputs["Value"].default_value = 0.79
        grade.inputs["Fac"].default_value = 1.0
        tree.links.remove(link)
        tree.links.new(source_socket, grade.inputs["Color"])
        tree.links.new(grade.outputs["Color"], base)
    return {"material": material.name, "adjusted": True, "grade_value": 0.79}


def setup_portrait():
    scene = bpy.context.scene
    for obj in [item for item in bpy.data.objects if item.type == "LIGHT"]:
        bpy.data.objects.remove(obj, do_unlink=True)
    lights = (
        ("V274H_KEY", (-0.72, -1.05, 2.07), 205.0, 0.95, (1.0, 0.91, 0.84)),
        ("V274H_FILL", (0.86, -0.74, 1.76), 78.0, 0.80, (0.72, 0.82, 1.0)),
        ("V274H_RIM", (0.42, 0.48, 2.02), 130.0, 0.72, (1.0, 0.72, 0.52)),
    )
    target = Vector((0.0, -0.035, 1.655))
    for name, location, energy, size, color in lights:
        data = bpy.data.lights.new(name + "_DATA", "AREA")
        data.energy, data.shape, data.size, data.color = energy, "DISK", size, color
        light = bpy.data.objects.new(name, data)
        scene.collection.objects.link(light)
        light.location = location
        point_at(light, target)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 768
    scene.render.resolution_y = 768
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.world.color = (0.006, 0.005, 0.005)
    scene.view_settings.look = "AgX - Medium High Contrast"
    camera = bpy.data.objects["V276E_CAMERA"]
    scene.camera = camera
    camera.data.lens = 96.0
    camera.location = Vector((0.0, -1.47, 1.67))
    point_at(camera, target)
    return camera, target


def clear_controls(keys):
    for key in keys:
        if key.name.startswith("CTRL_"):
            key.value = 0.0
    bpy.context.view_layer.update()


def render_pose(scene, keys, label, values):
    clear_controls(keys)
    for name, value in values.items():
        keys[name].value = value
    bpy.context.view_layer.update()
    path = RENDERS / f"v274h_{label}.png"
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return {
        "path": str(path.relative_to(ROOT)),
        "sha256": sha(path),
        "controls": values,
    }


def main():
    # Always reset the live scene so a failed MCP attempt cannot accumulate
    # half-applied material or groom edits.
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    for folder in (STAGE, RENDERS, AUDIT):
        folder.mkdir(parents=True, exist_ok=True)
    donor = bpy.data.objects[DONOR]
    driver = bpy.data.objects[DRIVER]
    donor.hide_render = False
    driver.hide_render = True
    groom_record = refine_groom()
    skin_record = refine_skin()
    scene = bpy.context.scene
    camera, target = setup_portrait()
    keys = driver.data.shape_keys.key_blocks

    basis = [tuple(point.co) for point in donor.data.shape_keys.key_blocks["Basis"].data]
    poses = {
        "neutral": {},
        "smile": {"CTRL_Smile": 1.0},
        "blink": {"CTRL_Blink_L": 1.0, "CTRL_Blink_R": 1.0},
        "jaw_open": {"CTRL_JawOpen": 0.72},
        "phoneme_o": {"CTRL_Phoneme_O": 0.90, "CTRL_JawOpen": 0.20},
        "phoneme_e": {"CTRL_Phoneme_E": 0.90},
        "phoneme_m": {"CTRL_Phoneme_M": 0.90},
    }
    renders = {label: render_pose(scene, keys, label, values) for label, values in poses.items()}

    clear_controls(keys)
    bpy.context.view_layer.update()
    returned = [tuple(point.co) for point in donor.data.shape_keys.key_blocks["Basis"].data]
    neutral_error = max(
        (Vector(a) - Vector(b)).length for a, b in zip(basis, returned)
    )
    # A restrained three-quarter neutral confirms the profile without changing
    # the proof camera used by the expression matrix.
    camera.location = Vector((-0.80, -1.15, 1.675))
    point_at(camera, target)
    path = RENDERS / "v274h_neutral_three_quarter.png"
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    renders["neutral_three_quarter"] = {
        "path": str(path.relative_to(ROOT)), "sha256": sha(path), "controls": {}
    }
    camera.location = Vector((0.0, -1.47, 1.67))
    point_at(camera, target)

    scene["V274H_STATUS"] = "IDENTITY_EXPRESSION_PROOF_VISUAL_REVIEW_REQUIRED"
    scene["V274H_NEUTRAL_RETURN_MAX_ERROR_M"] = neutral_error
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v274h-identity-expression-proof-v1",
        "status": "BUILT_VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)},
        "groom": groom_record,
        "skin": skin_record,
        "renders": renders,
        "neutral_return_max_error_m": neutral_error,
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha(OUTPUT)},
    }
    audit_path = AUDIT / "v274h_identity_expression_proof.json"
    audit_path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V274H_IDENTITY_EXPRESSION_PROOF_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
