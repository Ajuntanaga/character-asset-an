"""Add a reference-directed skin, eye, hair, brow, and beard lookdev pass to V276J."""

from __future__ import annotations

from pathlib import Path
import hashlib
import json
import math
import random
import sys

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.build_v204_groom import Surface, curl_strand, hair_material, make_curve_object, short_strand


SOURCE = ROOT / "production_v276j_corrected_facial_controls" / "Character_An_corrected_facial_controls_v276j.blend"
STAGE = ROOT / "production_v274a_identity_lookdev"
OUTPUT = STAGE / "Character_An_identity_lookdev_v274a.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"
HEAD = "V276E_GEO-head_animation_realistic"
JAW = "V276E_Jaw - Realistic"


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            digest.update(block)
    return digest.hexdigest()


def assign_single(obj, material):
    obj.data.materials.clear()
    obj.data.materials.append(material)


def skin_material():
    material = bpy.data.materials.new("V274A_SKIN_PHYSICAL")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    shader.name = "V274A_SKIN_PRINCIPLED"
    shader.subsurface_method = "RANDOM_WALK"
    shader.inputs["Roughness"].default_value = 0.48
    shader.inputs["IOR"].default_value = 1.40
    shader.inputs["Specular IOR Level"].default_value = 0.28
    shader.inputs["Subsurface Weight"].default_value = 0.095
    shader.inputs["Subsurface Radius"].default_value = (1.0, 0.42, 0.20)
    shader.inputs["Subsurface Scale"].default_value = 0.00125

    coordinates = nodes.new("ShaderNodeTexCoord")
    macro = nodes.new("ShaderNodeTexNoise")
    macro.name = "V274A_SKIN_MACRO"
    macro.inputs["Scale"].default_value = 4.2
    macro.inputs["Detail"].default_value = 3.0
    macro.inputs["Roughness"].default_value = 0.62
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.name = "V274A_SKIN_TONE_RAMP"
    ramp.color_ramp.elements[0].position = 0.23
    ramp.color_ramp.elements[0].color = (0.055, 0.012, 0.0045, 1.0)
    ramp.color_ramp.elements[1].position = 0.78
    ramp.color_ramp.elements[1].color = (0.245, 0.072, 0.025, 1.0)
    pores = nodes.new("ShaderNodeTexNoise")
    pores.name = "V274A_SKIN_PORES"
    pores.noise_dimensions = "3D"
    pores.inputs["Scale"].default_value = 235.0
    pores.inputs["Detail"].default_value = 5.0
    pores.inputs["Roughness"].default_value = 0.74
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.12
    bump.inputs["Distance"].default_value = 0.00016
    roughness = nodes.new("ShaderNodeMapRange")
    roughness.inputs["From Min"].default_value = 0.0
    roughness.inputs["From Max"].default_value = 1.0
    roughness.inputs["To Min"].default_value = 0.40
    roughness.inputs["To Max"].default_value = 0.58
    links.new(coordinates.outputs["Generated"], macro.inputs["Vector"])
    links.new(coordinates.outputs["Generated"], pores.inputs["Vector"])
    links.new(macro.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], shader.inputs["Base Color"])
    links.new(pores.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    links.new(pores.outputs["Fac"], roughness.inputs["Value"])
    links.new(roughness.outputs["Result"], shader.inputs["Roughness"])
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    return material


def simple_material(name, color, roughness, metallic=0.0):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = color
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Metallic"].default_value = metallic
    return material


def make_pupil(name, eye, material):
    center = eye.matrix_world.translation
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, location=(center.x, center.y - 0.0150, center.z))
    pupil = bpy.context.object
    pupil.name = name
    pupil.scale = (0.0037, 0.00055, 0.0037)
    assign_single(pupil, material)
    pupil.parent = eye
    pupil.matrix_parent_inverse = eye.matrix_world.inverted()
    return pupil


def add_poly(curve, points, start=1.0, end=0.15):
    spline = curve.data.splines.new("POLY")
    spline.points.add(len(points) - 1)
    denominator = max(1, len(points) - 1)
    for index, point in enumerate(points):
        spline.points[index].co = (*point, 1.0)
        spline.points[index].radius = start + (end - start) * index / denominator


def curve_object(name, bevel, material, collection):
    data = bpy.data.curves.new(f"{name}_DATA", "CURVE")
    data.dimensions = "3D"
    data.resolution_u = 1
    data.bevel_depth = bevel
    data.bevel_resolution = 2
    data.materials.append(material)
    obj = bpy.data.objects.new(name, data)
    collection.objects.link(obj)
    return obj


def parent_world_space(obj, parent):
    obj.parent = parent
    obj.matrix_parent_inverse = parent.matrix_world.inverted()


def point_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def area_light(name, location, energy, size, color):
    data = bpy.data.lights.new(name + "_DATA", "AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size
    data.color = color
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = Vector(location)
    point_at(obj, Vector((0.0, -0.02, 1.64)))
    return obj


def main():
    if Path(bpy.data.filepath).resolve() != SOURCE.resolve():
        raise RuntimeError(f"Open V276J first: {SOURCE}")
    for folder in (STAGE, RENDERS, AUDIT):
        folder.mkdir(parents=True, exist_ok=True)
    head = bpy.data.objects[HEAD]
    assign_single(head, skin_material())

    sclera_material = simple_material("V274A_SCLERA", (0.72, 0.62, 0.52, 1.0), 0.22)
    sclera_shader = sclera_material.node_tree.nodes.get("Principled BSDF")
    sclera_shader.inputs["Subsurface Weight"].default_value = 0.035
    sclera_shader.inputs["IOR"].default_value = 1.38
    iris_material = simple_material("V274A_IRIS_BROWN", (0.045, 0.012, 0.0035, 1.0), 0.24)
    iris_shader = iris_material.node_tree.nodes.get("Principled BSDF")
    iris_shader.inputs["Coat Weight"].default_value = 0.16
    iris_shader.inputs["Coat Roughness"].default_value = 0.08
    pupil_material = simple_material("V274A_PUPIL", (0.0003, 0.0001, 0.00005, 1.0), 0.12)
    pupils = []
    for side in ("L", "R"):
        sclera = bpy.data.objects[f"V276E_GEO-head_animation_realistic.sclera.{side}"]
        iris = bpy.data.objects[f"V276E_GEO-head_animation_realistic.iris.{side}"]
        assign_single(sclera, sclera_material)
        assign_single(iris, iris_material)
        pupils.append(make_pupil(f"V274A_PUPIL_{side}", sclera, pupil_material))

    if JAW in bpy.data.objects:
        assign_single(bpy.data.objects[JAW], simple_material("V274A_ORAL", (0.36, 0.15, 0.10, 1.0), 0.44))

    collection = bpy.data.collections.new("V274A_GROOM")
    bpy.context.scene.collection.children.link(collection)
    hair_mat = hair_material("V274A_HAIR", 0.95, 0.44, (0.0016, 0.0009, 0.00045, 1.0))
    highlight_mat = hair_material("V274A_HAIR_HIGHLIGHT", 0.88, 0.40, (0.0050, 0.0024, 0.0010, 1.0))
    facial_mat = hair_material("V274A_FACIAL_HAIR", 0.92, 0.52, (0.0022, 0.0011, 0.0006, 1.0))
    surface = Surface(head)

    rng = random.Random(27401)
    scalp_roots = []
    attempts = 0
    while len(scalp_roots) < 4200 and attempts < 280000:
        attempts += 1
        phi = rng.uniform(-math.pi, math.pi)
        theta = rng.uniform(0.10, 1.53)
        candidate = Vector((
            0.101 * math.sin(theta) * math.cos(phi),
            0.002 + 0.105 * math.sin(theta) * math.sin(phi),
            1.703 + 0.101 * math.cos(theta),
        ))
        frontness = max(0.0, min(1.0, (-candidate.y - 0.005) / 0.095))
        temple = max(0.0, min(1.0, (abs(candidate.x) - 0.058) / 0.035))
        hairline = 1.714 + 0.020 * frontness - 0.026 * temple
        if candidate.y < 0.028 and candidate.z < hairline:
            continue
        if candidate.y < 0.018 and candidate.z > 1.723 and abs(candidate.x - 0.034) < 0.0045:
            continue
        root, normal = surface.nearest(candidate)
        if root.z < 1.635 or root.z > 1.810:
            continue
        scalp_roots.append((root, normal, rng.random() * math.tau))
    if len(scalp_roots) != 4200:
        raise RuntimeError(f"Only created {len(scalp_roots)} scalp roots")

    undercoat = []
    curls = []
    highlights = []
    for index, (root, normal, phase) in enumerate(scalp_roots):
        side = -1.0 if root.x < 0.034 else 1.0
        taper = max(0.34, min(1.0, (root.z - 1.645) / 0.105))
        lean = Vector((side * rng.uniform(0.001, 0.004), rng.uniform(-0.0010, 0.0007), -rng.uniform(0.0, 0.0015)))
        undercoat.append(curl_strand(root, normal, 0.0065 * taper, 0.0011 * taper, phase, 0.72, lean, 6))
        if index % 3 == 0:
            curls.append(curl_strand(root, normal, rng.uniform(0.012, 0.021) * taper, rng.uniform(0.0020, 0.0030) * taper, phase, rng.uniform(1.05, 1.38), lean, 8))
        if index % 17 == 0:
            highlights.append(curl_strand(root, normal, rng.uniform(0.016, 0.025) * taper, rng.uniform(0.0014, 0.0022) * taper, phase, rng.uniform(1.2, 1.55), lean, 8))
    groom_objects = [
        make_curve_object("V274A_HAIR_UNDERCOAT", undercoat, 0.000075, hair_mat, collection, len(undercoat)),
        make_curve_object("V274A_HAIR_CURLS", curls, 0.000095, hair_mat, collection, len(curls)),
        make_curve_object("V274A_HAIR_HIGHLIGHTS", highlights, 0.000055, highlight_mat, collection, len(highlights)),
    ]

    def nearest_face(x, z):
        root, normal = surface.nearest(Vector((x, -0.145, z)))
        if root.y > -0.055:
            raise RuntimeError(f"Facial groom root missed face at {(x, z)} -> {tuple(root)}")
        return root, normal

    brow_strands = []
    rng = random.Random(27420)
    for side in (-1, 1):
        for _ in range(170):
            t = rng.random()
            x = side * (0.018 + 0.050 * t)
            z = 1.708 + 0.009 * math.sin(math.pi * t) + rng.uniform(-0.0018, 0.0018)
            root, normal = nearest_face(x, z)
            brow_strands.append(short_strand(root, normal, rng.uniform(0.0045, 0.0070), Vector((side * 0.0030, -0.0004, 0.0010)), rng.random() * math.tau, 4))
    groom_objects.append(make_curve_object("V274A_BROWS", brow_strands, 0.000055, facial_mat, collection, len(brow_strands)))

    beard_strands = []
    rng = random.Random(27430)
    attempts = 0
    while len(beard_strands) < 2100 and attempts < 120000:
        attempts += 1
        region = rng.random()
        if region < 0.54:
            z = rng.uniform(1.500, 1.570)
            width = rng.uniform(0.018, 0.088)
            x = rng.choice((-1.0, 1.0)) * width
        elif region < 0.88:
            z = rng.uniform(1.555, 1.635)
            x = rng.choice((-1.0, 1.0)) * rng.uniform(0.038, 0.091)
        else:
            z = rng.uniform(1.575, 1.605)
            x = rng.choice((-1.0, 1.0)) * rng.uniform(0.010, 0.054)
        if 1.552 < z < 1.588 and abs(x) < 0.041:
            continue
        root, normal = nearest_face(x, z)
        length = rng.uniform(0.0020, 0.0056) * (1.25 if z < 1.545 else 1.0)
        lean = Vector((rng.uniform(-0.0008, 0.0008), -0.0002, -length * 0.22))
        beard_strands.append(short_strand(root, normal, length, lean, rng.random() * math.tau, 4))
    groom_objects.append(make_curve_object("V274A_BEARD_STUBBLE", beard_strands, 0.000045, facial_mat, collection, len(beard_strands)))

    mustache_strands = []
    rng = random.Random(27440)
    for side in (-1, 1):
        for _ in range(180):
            x = side * rng.uniform(0.008, 0.050)
            t = (abs(x) - 0.008) / 0.042
            z = 1.603 + 0.009 * (1.0 - t) + rng.uniform(-0.0020, 0.0020)
            root, normal = nearest_face(x, z)
            mustache_strands.append(short_strand(root, normal, rng.uniform(0.0030, 0.0064), Vector((side * 0.0020, -0.0003, -0.0018)), rng.random() * math.tau, 4))
    groom_objects.append(make_curve_object("V274A_MUSTACHE", mustache_strands, 0.000047, facial_mat, collection, len(mustache_strands)))

    mark_material = simple_material("V274A_GLABELLA_MARK", (0.030, 0.007, 0.003, 1.0), 0.58)
    marks = curve_object("V274A_GLABELLA_MARKS", 0.00045, mark_material, collection)
    for offset in (-0.0065, 0.0, 0.0065):
        root, normal = nearest_face(offset, 1.735)
        tangent = Vector((0.0, 0.0, 1.0))
        add_poly(marks, [root, root + tangent * 0.011 + normal * 0.00025], 0.75, 0.20)
    groom_objects.append(marks)
    for obj in groom_objects:
        parent_world_space(obj, head)

    for old in [item for item in bpy.data.objects if item.type == "LIGHT"]:
        bpy.data.objects.remove(old, do_unlink=True)
    area_light("V274A_KEY", (-0.80, -1.30, 2.25), 720.0, 1.20, (1.0, 0.73, 0.55))
    area_light("V274A_FILL", (0.95, -0.90, 1.82), 390.0, 1.00, (0.48, 0.64, 1.0))
    area_light("V274A_RIM", (0.45, 0.55, 2.08), 560.0, 0.80, (1.0, 0.54, 0.30))

    camera = bpy.data.objects["V276E_CAMERA"]
    scene = bpy.context.scene
    scene.camera = camera
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.resolution_percentage = 100
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.world.color = (0.006, 0.006, 0.008)
    scene.render.resolution_x = 900
    scene.render.resolution_y = 900
    target = Vector((0.0, -0.02, 1.645))
    views = {
        "front": (Vector((0.0, -1.52, 1.650)), 78.0),
        "left_three_quarter": (Vector((-0.82, -1.20, 1.675)), 82.0),
        "left_profile": (Vector((-1.52, -0.02, 1.660)), 88.0),
    }
    render_records = {}
    for label, (location, lens) in views.items():
        camera.location = location
        camera.data.lens = lens
        point_at(camera, target)
        path = RENDERS / f"v274a_{label}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        render_records[label] = {"path": str(path.relative_to(ROOT)), "sha256": sha256(path)}

    scene["V274A_STATUS"] = "IDENTITY_LOOKDEV_VISUAL_REVIEW_REQUIRED"
    scene["V274A_GROOM_COUNTS"] = json.dumps({obj.name: len(obj.data.splines) for obj in groom_objects})
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v274a-identity-lookdev-v1",
        "status": "BUILT_VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha256(SOURCE)},
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha256(OUTPUT)},
        "head": HEAD,
        "groom_counts": {obj.name: len(obj.data.splines) for obj in groom_objects},
        "eye_components": [obj.name for obj in pupils],
        "renders": render_records,
    }
    (AUDIT / "v274a_identity_lookdev.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V274A_IDENTITY_LOOKDEV_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
