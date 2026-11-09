"""Build a conservative reference-shaped identity and repair the eye seating."""

from pathlib import Path
import hashlib
import json
import math

import bpy
import bmesh
from mathutils import Matrix, Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v276j_corrected_facial_controls" / "Character_An_corrected_facial_controls_v276j.blend"
STAGE = ROOT / "production_v274c_reference_identity_sculpt"
OUTPUT = STAGE / "Character_An_reference_identity_v274c.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"
HEAD = "V276E_GEO-head_animation_realistic"


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            digest.update(block)
    return digest.hexdigest()


def gaussian(value, center, radius):
    return math.exp(-((value - center) / radius) ** 2)


def point_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def make_material(name, color, roughness=0.45, specular=0.45):
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = color
    shader.inputs["Roughness"].default_value = roughness
    if "Specular IOR Level" in shader.inputs:
        shader.inputs["Specular IOR Level"].default_value = specular
    return material


def make_uv_sphere(name, radius, segments, rings):
    mesh = bpy.data.meshes.new(name + "_MESH")
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=rings, radius=radius)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def sculpt(world):
    p = world.copy()
    # Only the anterior face receives identity work. This protects cranium,
    # ears, neck, rig attachments, and the existing animation topology.
    anterior = gaussian(world.y, -0.112, 0.050)
    if anterior < 0.002 or world.z < 1.465 or world.z > 1.755:
        return p

    side_sign = 1.0 if world.x >= 0.0 else -1.0
    abs_x = abs(world.x)

    # Reference: broader lower face, rounded but substantial jaw and chin.
    jaw = gaussian(world.z, 1.535, 0.060) * gaussian(abs_x, 0.070, 0.055) * anterior
    p.x += side_sign * 0.0105 * jaw
    chin = gaussian(world.z, 1.505, 0.036) * gaussian(abs_x, 0.032, 0.042) * anterior
    p.x += side_sign * 0.0050 * chin
    p.y -= 0.0020 * chin

    # Reference: stronger zygomatic width and fuller mid-face.
    cheek = gaussian(world.z, 1.625, 0.047) * gaussian(abs_x, 0.078, 0.036) * anterior
    p.x += side_sign * 0.0090 * cheek
    p.y -= 0.0040 * cheek

    # Reference: wider alar base with a stronger, rounder nasal tip.
    nose_base = gaussian(world.z, 1.615, 0.025) * gaussian(abs_x, 0.025, 0.025) * anterior
    p.x += side_sign * (0.0025 + abs_x * 0.10) * nose_base
    nose_tip = gaussian(world.z, 1.638, 0.028) * gaussian(abs_x, 0.012, 0.023) * anterior
    p.y -= 0.0045 * nose_tip

    # Reference: wider, fuller lips, especially the lower lip.
    mouth = gaussian(world.z, 1.570, 0.020) * gaussian(abs_x, 0.032, 0.040) * anterior
    p.x += side_sign * 0.0045 * mouth * min(1.0, abs_x / 0.025 + 0.20)
    p.y -= 0.0035 * mouth
    lower_lip = gaussian(world.z, 1.558, 0.010) * gaussian(abs_x, 0.025, 0.038) * anterior
    p.y -= 0.0020 * lower_lip

    # Reference: heavy glabella and hooded upper-eye structure.
    brow = gaussian(world.z, 1.708, 0.025) * gaussian(abs_x, 0.045, 0.055) * anterior
    p.y -= 0.0040 * brow
    inner_brow = gaussian(world.z, 1.704, 0.024) * gaussian(abs_x, 0.018, 0.022) * anterior
    p.y -= 0.0030 * inner_brow
    p.z -= 0.0018 * inner_brow
    upper_lid = gaussian(world.z, 1.688, 0.015) * gaussian(abs_x, 0.040, 0.030) * anterior
    p.z -= 0.0012 * upper_lid
    p.y -= 0.0015 * upper_lid

    # Mild vertical compression removes the generic elongated mask quality.
    face_core = gaussian(abs_x, 0.045, 0.090) * gaussian(world.z, 1.615, 0.125) * anterior
    p.z += (1.615 - world.z) * 0.025 * face_core
    return p


def main():
    if Path(bpy.data.filepath).resolve() != SOURCE.resolve():
        bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    for folder in (STAGE, RENDERS, AUDIT):
        folder.mkdir(parents=True, exist_ok=True)

    scene = bpy.context.scene
    scene.frame_set(1)
    head = bpy.data.objects[HEAD]
    keys = head.data.shape_keys.key_blocks
    identity = keys["IDENTITY_LANDMARK_WARP"]
    for key in keys:
        key.value = 1.0 if key == identity else 0.0
    bpy.context.view_layer.update()

    prior = keys.get("IDENTITY_REFERENCE_SCULPT_V274C")
    if prior:
        head.shape_key_remove(prior)
    refined = head.shape_key_add(name="IDENTITY_REFERENCE_SCULPT_V274C", from_mix=True)
    refined.relative_key = identity
    inverse = head.matrix_world.inverted()
    moved = 0
    maximum = 0.0
    total = 0.0
    for point in refined.data:
        world = head.matrix_world @ point.co
        destination = sculpt(world)
        distance = (destination - world).length
        if distance > 1e-7:
            point.co = inverse @ destination
            moved += 1
            maximum = max(maximum, distance)
            total += distance
    refined.value = 1.0

    # Reseat complete eye roots at the eyelid aperture plane. The inherited
    # V274/V276 eyes sat 9-12 mm behind it, which produced black cavities.
    eye_records = {}
    for side, center_x in (("L", 0.043), ("R", -0.043)):
        sclera = bpy.data.objects[f"V276E_GEO-head_animation_realistic.sclera.{side}"]
        inherited_iris = bpy.data.objects[f"V276E_GEO-head_animation_realistic.iris.{side}"]
        inherited_iris.hide_render = True
        sclera_world = sclera.matrix_world.copy()
        sclera_world.translation.x = center_x
        sclera_world.translation.y = -0.1050
        sclera_world.translation.z = 1.6680
        sclera.matrix_world = sclera_world
        iris = make_uv_sphere(f"V274C_IRIS_{side}", 0.0050, 40, 20)
        iris.location = (center_x, -0.11850, 1.6610)
        iris.scale = (1.0, 0.16, 1.0)
        pupil = make_uv_sphere(f"V274C_PUPIL_{side}", 0.00190, 36, 18)
        pupil.location = (center_x, -0.11935, 1.6610)
        pupil.scale = (1.0, 0.12, 1.0)
        eye_records[side] = {
            "sclera_center": list(sclera.matrix_world.translation),
            "iris_center": list(iris.matrix_world.translation),
            "pupil_center": list(pupil.matrix_world.translation),
        }

    clay = make_material("V274C_IDENTITY_CLAY", (0.24, 0.105, 0.050, 1.0), 0.52, 0.32)
    sclera_mat = make_material("V274C_SCLERA", (0.78, 0.68, 0.56, 1.0), 0.28, 0.48)
    iris_mat = make_material("V274C_IRIS_BROWN", (0.095, 0.024, 0.006, 1.0), 0.30, 0.48)
    pupil_mat = make_material("V274C_PUPIL", (0.002, 0.001, 0.001, 1.0), 0.18, 0.52)
    head.data.materials.clear()
    head.data.materials.append(clay)
    for side in ("L", "R"):
        for name, material in (
            (f"V276E_GEO-head_animation_realistic.sclera.{side}", sclera_mat),
            (f"V274C_IRIS_{side}", iris_mat),
            (f"V274C_PUPIL_{side}", pupil_mat),
        ):
            obj = bpy.data.objects.get(name)
            if obj:
                obj.data.materials.clear()
                obj.data.materials.append(material)
                obj.hide_render = False

    # Hide comparison meshes and leave the animation head hierarchy visible.
    for obj in bpy.data.objects:
        if obj.type == "MESH" and not (
            obj == head
            or obj.name.startswith("V276E_GEO-head_animation_realistic.")
            or obj.name.startswith("V274C_IRIS_")
            or obj.name.startswith("V274C_PUPIL_")
            or obj.name.startswith("V276E_Jaw")
        ):
            obj.hide_render = True
    for polygon in head.data.polygons:
        polygon.use_smooth = True
    subdivision = head.modifiers.get("V274C_PORTRAIT_SUBDIV") or head.modifiers.new("V274C_PORTRAIT_SUBDIV", "SUBSURF")
    subdivision.levels = 2
    subdivision.render_levels = 2

    for obj in [item for item in bpy.data.objects if item.type == "LIGHT"]:
        obj.hide_render = True
    lights = (
        ("V274C_KEY", "AREA", Vector((-0.65, -0.90, 2.12)), 430.0, 0.75),
        ("V274C_FILL", "AREA", Vector((0.72, -0.72, 1.78)), 185.0, 0.62),
        ("V274C_RIM", "AREA", Vector((0.22, 0.42, 1.92)), 260.0, 0.52),
    )
    for name, light_type, location, energy, size in lights:
        data = bpy.data.lights.new(name, light_type)
        data.energy = energy
        data.shape = "DISK"
        data.size = size
        light = bpy.data.objects.new(name, data)
        scene.collection.objects.link(light)
        light.location = location
        point_at(light, Vector((0.0, -0.04, 1.62)))

    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 960
    scene.render.resolution_y = 960
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.look = "AgX - Medium High Contrast"
    camera = bpy.data.objects["V276E_CAMERA"]
    scene.camera = camera
    target = Vector((0.0, -0.055, 1.635))
    views = {
        "front": (Vector((0.0, -1.42, 1.635)), 92.0),
        "left_three_quarter": (Vector((-0.78, -1.13, 1.650)), 92.0),
        "left_profile": (Vector((-1.42, -0.01, 1.635)), 96.0),
        "eye_close": (Vector((0.0, -0.72, 1.690)), 112.0),
    }
    renders = {}
    for label, (location, lens) in views.items():
        camera.location = location
        camera.data.lens = lens
        point_at(camera, Vector((0.0, -0.105, 1.684)) if label == "eye_close" else target)
        path = RENDERS / f"v274c_{label}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        renders[label] = str(path.relative_to(ROOT))

    scene["V274C_STATUS"] = "REFERENCE_IDENTITY_AND_EYES_VISUAL_REVIEW_REQUIRED"
    scene["V274C_IDENTITY_SHAPE"] = refined.name
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v274c-reference-identity-v1",
        "status": "BUILT_VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)},
        "shape_key": refined.name,
        "sculpt": {"moved_vertices": moved, "mean_m": total / max(1, moved), "max_m": maximum},
        "eyes": eye_records,
        "renders": renders,
        "output": {"path": str(OUTPUT.relative_to(ROOT))},
    }
    record["output"]["sha256"] = sha(OUTPUT)
    (AUDIT / "v274c_reference_identity.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V274C_REFERENCE_IDENTITY_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
