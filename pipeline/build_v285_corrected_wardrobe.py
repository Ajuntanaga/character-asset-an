"""Correct V283 wardrobe without the detached V284 trim/toe experiments."""

from pathlib import Path
import hashlib
import json
import math

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v283_anatomical_wardrobe" / "Character_An_anatomical_wardrobe_v283.blend"
STAGE = ROOT / "production_v285_corrected_wardrobe"
OUTPUT = STAGE / "Character_An_corrected_wardrobe_v285.blend"
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


def smooth_first(obj, factor, iterations):
    modifier = obj.modifiers.new("V285_RELAX_TAILORING", "SMOOTH")
    modifier.factor = factor
    modifier.iterations = iterations
    obj.modifiers.move(len(obj.modifiers) - 1, 0)


def waist_underlayer(material_value, rig):
    segments = 64
    rings = [(0.91, .185, .126), (1.00, .192, .132), (1.07, .195, .134)]
    vertices = []
    for z, rx, ry in rings:
        vertices.extend((rx * math.cos(2 * math.pi * i / segments), .005 + ry * math.sin(2 * math.pi * i / segments), z) for i in range(segments))
    faces = []
    for ring in range(len(rings) - 1):
        for index in range(segments):
            nxt = (index + 1) % segments
            faces.append((ring * segments + index, ring * segments + nxt, (ring + 1) * segments + nxt, (ring + 1) * segments + index))
    mesh = bpy.data.meshes.new("V285_SHIRT_UNDERLAYER_MESH")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    mesh.materials.append(material_value)
    obj = bpy.data.objects.new("V285_SHIRT_WAIST_UNDERLAYER", mesh)
    bpy.context.scene.collection.objects.link(obj)
    solid = obj.modifiers.new("V285_SHIRT_THICKNESS", "SOLIDIFY")
    solid.thickness = .003
    armature = obj.modifiers.new("V285_RIG", "ARMATURE")
    armature.object = rig
    for source_group in bpy.data.objects["V211_BODY_NEUTRAL"].vertex_groups:
        if source_group.name.startswith("DEF-spine") or source_group.name.startswith("DEF-pelvis"):
            group = obj.vertex_groups.new(name=source_group.name)
            group.add(list(range(len(vertices))), 0.5, "ADD")
    return obj


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
    for name in ("V283_BOOT_SOLE_L", "V283_BOOT_SOLE_R"):
        obj = bpy.data.objects.get(name)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)
    rig = bpy.data.objects[RIG]
    jacket = bpy.data.objects["V283_FITTED_DENIM_JACKET"]
    shirt = bpy.data.objects["V283_TAILORED_SHIRT"]
    trousers = bpy.data.objects["V283_TAILORED_TROUSERS"]
    boots = bpy.data.objects["V283_CHELSEA_BOOT_UPPERS"]
    denim = material("V285_SMOKED_INDIGO_DENIM", (.009, .014, .021), (.050, .073, .102), .70, 135.0)
    floral = material("V285_OXBLOOD_FLORAL", (.030, .003, .007), (.36, .058, .020), .61, 14.0)
    wool = material("V285_BLACK_WOOL", (.005, .006, .008), (.026, .030, .038), .77, 120.0)
    leather = material("V285_CHESTNUT_LEATHER", (.022, .005, .002), (.14, .030, .007), .40, 30.0)
    for obj, mat in ((jacket, denim), (shirt, floral), (trousers, wool), (boots, leather)):
        obj.data.materials.clear(); obj.data.materials.append(mat)
    smooth_first(jacket, .38, 4)
    smooth_first(shirt, .22, 3)
    smooth_first(trousers, .20, 3)
    smooth_first(boots, .72, 10)
    for vertex in trousers.data.vertices:
        axis = .093 if vertex.co.x >= 0 else -.093
        vertex.co.x = axis + (vertex.co.x - axis) * 1.065
        vertex.co.y = .005 + (vertex.co.y - .005) * 1.05
    underlayer = waist_underlayer(floral, rig)

    scene = bpy.context.scene
    camera = bpy.data.objects["V283_FULL_CAMERA"]
    camera.name = "V285_FULL_CAMERA"
    camera.location = Vector((0.0, -5.25, 1.00))
    point_at(camera, Vector((0.0, 0.0, .93)))
    renders = {"front": render(scene, camera, RENDERS / "v285_corrected_front.png")}
    camera.location = Vector((-3.0, -4.25, 1.12))
    point_at(camera, Vector((0.0, 0.0, .98)))
    renders["three_quarter"] = render(scene, camera, RENDERS / "v285_corrected_three_quarter.png")
    scene["V285_STATUS"] = "CORRECTED_WARDROBE_BASELINE"
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v285-corrected-wardrobe-v1",
        "status": "CORRECTED_BASELINE_VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)},
        "removed_detached_solids": ["V283_BOOT_SOLE_L", "V283_BOOT_SOLE_R"],
        "underlayer": underlayer.name,
        "renders": renders,
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha(OUTPUT)},
    }
    (AUDIT / "v285_corrected_wardrobe.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V285_CORRECTED_WARDROBE_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
