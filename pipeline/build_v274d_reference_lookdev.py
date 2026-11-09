"""Apply reference-weighted skin and a clustered curl groom to V274C."""

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

SOURCE = ROOT / "production_v274c_reference_identity_sculpt" / "Character_An_reference_identity_v274c.blend"
STAGE = ROOT / "production_v274d_reference_lookdev"
OUTPUT = STAGE / "Character_An_reference_lookdev_v274d.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"
HEAD = "V276E_GEO-head_animation_realistic"


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            digest.update(block)
    return digest.hexdigest()


def assign(obj, material):
    obj.data.materials.clear()
    obj.data.materials.append(material)


def point_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def parent_keep_world(obj, parent):
    matrix = obj.matrix_world.copy()
    obj.parent = parent
    obj.matrix_world = matrix


def simple_material(name, color, roughness, specular=0.35):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = color
    shader.inputs["Roughness"].default_value = roughness
    if "Specular IOR Level" in shader.inputs:
        shader.inputs["Specular IOR Level"].default_value = specular
    return mat


def skin_material():
    mat = bpy.data.materials.get("V274D_SKIN") or bpy.data.materials.new("V274D_SKIN")
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    shader.inputs["Roughness"].default_value = 0.47
    shader.inputs["IOR"].default_value = 1.40
    shader.inputs["Specular IOR Level"].default_value = 0.26
    shader.inputs["Subsurface Weight"].default_value = 0.055
    shader.inputs["Subsurface Radius"].default_value = (1.0, 0.42, 0.20)
    shader.inputs["Subsurface Scale"].default_value = 0.00075
    tex = nodes.new("ShaderNodeTexCoord")
    macro = nodes.new("ShaderNodeTexNoise")
    macro.inputs["Scale"].default_value = 5.2
    macro.inputs["Detail"].default_value = 2.4
    macro.inputs["Roughness"].default_value = 0.58
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.24
    ramp.color_ramp.elements[0].color = (0.028, 0.0065, 0.0022, 1.0)
    ramp.color_ramp.elements[1].position = 0.78
    ramp.color_ramp.elements[1].color = (0.135, 0.040, 0.012, 1.0)
    pores = nodes.new("ShaderNodeTexNoise")
    pores.inputs["Scale"].default_value = 320.0
    pores.inputs["Detail"].default_value = 3.0
    pores.inputs["Roughness"].default_value = 0.68
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.042
    bump.inputs["Distance"].default_value = 0.00007
    links.new(tex.outputs["Generated"], macro.inputs["Vector"])
    links.new(tex.outputs["Generated"], pores.inputs["Vector"])
    links.new(macro.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], shader.inputs["Base Color"])
    links.new(pores.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    return mat


def face_root(surface, x, z):
    root, normal = surface.nearest(Vector((x, -0.15, z)))
    if root.y > -0.045:
        raise RuntimeError(f"Face groom miss {(x, z)} -> {tuple(root)}")
    return root, normal


def main():
    if Path(bpy.data.filepath).resolve() != SOURCE.resolve():
        bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    for folder in (STAGE, RENDERS, AUDIT):
        folder.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    head = bpy.data.objects[HEAD]
    assign(head, skin_material())

    sclera_mat = simple_material("V274D_SCLERA", (0.72, 0.62, 0.50, 1.0), 0.30, 0.40)
    iris_mat = simple_material("V274D_IRIS", (0.105, 0.028, 0.006, 1.0), 0.25, 0.45)
    pupil_mat = simple_material("V274D_PUPIL", (0.001, 0.0004, 0.0002, 1.0), 0.17, 0.48)
    for side in ("L", "R"):
        assign(bpy.data.objects[f"V276E_GEO-head_animation_realistic.sclera.{side}"], sclera_mat)
        assign(bpy.data.objects[f"V274C_IRIS_{side}"], iris_mat)
        assign(bpy.data.objects[f"V274C_PUPIL_{side}"], pupil_mat)

    collection = bpy.data.collections.new("V274D_REFERENCE_GROOM")
    scene.collection.children.link(collection)
    hair_mat = hair_material("V274D_HAIR", 0.98, 0.38, (0.0012, 0.0007, 0.00035, 1.0))
    hair_hi = hair_material("V274D_HAIR_WARM", 0.92, 0.42, (0.0045, 0.0018, 0.00065, 1.0))
    facial_mat = hair_material("V274D_FACIAL", 0.97, 0.46, (0.0016, 0.00075, 0.00030, 1.0))
    surface = Surface(head)

    rng = random.Random(27440)
    roots = []
    attempts = 0
    while len(roots) < 1500 and attempts < 180000:
        attempts += 1
        phi = rng.uniform(-math.pi, math.pi)
        theta = rng.uniform(0.10, 1.48)
        candidate = Vector((
            0.108 * math.sin(theta) * math.cos(phi),
            0.004 + 0.108 * math.sin(theta) * math.sin(phi),
            1.700 + 0.107 * math.cos(theta),
        ))
        frontness = max(0.0, min(1.0, (-candidate.y + 0.006) / 0.11))
        temple = max(0.0, min(1.0, (abs(candidate.x) - 0.060) / 0.038))
        hairline = 1.712 + 0.026 * frontness - 0.018 * temple
        if candidate.y < 0.025 and candidate.z < hairline:
            continue
        # A clean diagonal part on character left (viewer right).
        part_x = -0.034 + (candidate.z - 1.72) * 0.20
        if candidate.y < 0.02 and abs(candidate.x - part_x) < 0.0042:
            continue
        root, normal = surface.nearest(candidate)
        if not 1.635 < root.z < 1.808:
            continue
        roots.append((root, normal, rng.random() * math.tau))

    undercoat, curls, highlights = [], [], []
    for index, (root, normal, phase) in enumerate(roots):
        front = max(0.0, min(1.0, (-root.y + 0.02) / 0.14))
        crown = max(0.0, min(1.0, (root.z - 1.69) / 0.11))
        length = 0.010 + 0.010 * crown + 0.003 * front
        radius = 0.0024 + 0.0013 * crown
        part_side = -1.0 if root.x < -0.034 else 1.0
        lean = Vector((part_side * (0.0025 + 0.0020 * front), -0.0007, -0.0010))
        undercoat.append(curl_strand(root, normal, length * 0.62, radius * 0.55, phase, 0.92, lean * 0.35, 7))
        curls.append(curl_strand(root, normal, length, radius, phase, rng.uniform(1.15, 1.48), lean, 10))
        if index % 9 == 0:
            highlights.append(curl_strand(root, normal, length * 1.08, radius * 0.82, phase + 0.7, 1.35, lean * 1.15, 10))
    groom = [
        make_curve_object("V274D_HAIR_BASE", undercoat, 0.00034, hair_mat, collection, len(undercoat)),
        make_curve_object("V274D_CURL_MASS", curls, 0.00058, hair_mat, collection, len(curls)),
        make_curve_object("V274D_CURL_HIGHLIGHTS", highlights, 0.00034, hair_hi, collection, len(highlights)),
    ]

    brows = []
    rng = random.Random(27441)
    for side in (-1, 1):
        for _ in range(230):
            t = rng.random()
            x = side * (0.018 + 0.052 * t)
            z = 1.701 + 0.009 * math.sin(math.pi * t) + rng.uniform(-0.0016, 0.0016)
            root, normal = face_root(surface, x, z)
            brows.append(short_strand(root, normal, rng.uniform(0.0045, 0.0078), Vector((side * 0.0030, -0.0005, 0.0010)), rng.random() * math.tau, 5))
    groom.append(make_curve_object("V274D_BROWS", brows, 0.000075, facial_mat, collection, len(brows)))

    beard = []
    rng = random.Random(27442)
    attempts = 0
    while len(beard) < 2200 and attempts < 160000:
        attempts += 1
        region = rng.random()
        if region < 0.60:
            z = rng.uniform(1.492, 1.580)
            x = rng.uniform(-0.093, 0.093)
        else:
            z = rng.uniform(1.555, 1.640)
            x = rng.choice((-1.0, 1.0)) * rng.uniform(0.042, 0.094)
        if 1.552 < z < 1.595 and abs(x) < 0.044:
            continue
        root, normal = face_root(surface, x, z)
        length = rng.uniform(0.0025, 0.0068) * (1.25 if z < 1.545 else 1.0)
        beard.append(short_strand(root, normal, length, Vector((rng.uniform(-0.0005, 0.0005), -0.0002, -length * 0.25)), rng.random() * math.tau, 4))
    groom.append(make_curve_object("V274D_BEARD", beard, 0.000050, facial_mat, collection, len(beard)))

    mustache = []
    rng = random.Random(27443)
    for side in (-1, 1):
        for _ in range(220):
            x = side * rng.uniform(0.008, 0.052)
            t = (abs(x) - 0.008) / 0.044
            z = 1.603 + 0.008 * (1.0 - t) + rng.uniform(-0.0018, 0.0018)
            root, normal = face_root(surface, x, z)
            mustache.append(short_strand(root, normal, rng.uniform(0.0032, 0.0066), Vector((side * 0.0022, -0.0002, -0.0018)), rng.random() * math.tau, 4))
    groom.append(make_curve_object("V274D_MUSTACHE", mustache, 0.000055, facial_mat, collection, len(mustache)))
    for obj in groom:
        parent_keep_world(obj, head)

    for light in [obj for obj in bpy.data.objects if obj.type == "LIGHT"]:
        bpy.data.objects.remove(light, do_unlink=True)
    for name, location, energy, size, color in (
        ("V274D_KEY", (-0.72, -1.05, 2.12), 410.0, 0.85, (1.0, 0.86, 0.74)),
        ("V274D_FILL", (0.82, -0.82, 1.82), 185.0, 0.72, (0.67, 0.78, 1.0)),
        ("V274D_RIM", (0.40, 0.48, 2.03), 300.0, 0.62, (1.0, 0.72, 0.52)),
    ):
        data = bpy.data.lights.new(name + "_DATA", "AREA")
        data.energy, data.shape, data.size, data.color = energy, "DISK", size, color
        light = bpy.data.objects.new(name, data)
        scene.collection.objects.link(light)
        light.location = location
        point_at(light, Vector((0.0, -0.035, 1.64)))

    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 960
    scene.render.resolution_y = 960
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.world.color = (0.012, 0.010, 0.009)
    camera = bpy.data.objects["V276E_CAMERA"]
    scene.camera = camera
    target = Vector((0.0, -0.055, 1.640))
    views = {
        "front": (Vector((0.0, -1.42, 1.640)), 90.0),
        "left_three_quarter": (Vector((-0.79, -1.12, 1.655)), 92.0),
        "left_profile": (Vector((-1.42, -0.01, 1.640)), 96.0),
    }
    renders = {}
    for label, (location, lens) in views.items():
        camera.location = location
        camera.data.lens = lens
        point_at(camera, target)
        path = RENDERS / f"v274d_{label}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        renders[label] = {"path": str(path.relative_to(ROOT)), "sha256": sha(path)}

    scene["V274D_STATUS"] = "REFERENCE_LOOKDEV_VISUAL_REVIEW_REQUIRED"
    scene["V274D_GROOM_COUNTS"] = json.dumps({obj.name: len(obj.data.splines) for obj in groom})
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v274d-reference-lookdev-v1",
        "status": "BUILT_VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)},
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha(OUTPUT)},
        "groom_counts": {obj.name: len(obj.data.splines) for obj in groom},
        "renders": renders,
    }
    (AUDIT / "v274d_reference_lookdev.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V274D_REFERENCE_LOOKDEV_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
