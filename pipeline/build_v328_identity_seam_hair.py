"""Repair V327 head/body integration and replace the rejected legacy groom."""

from pathlib import Path
import hashlib
import json
import math
import random

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v327_photoreal_identity_integration" / "Character_An_photoreal_identity_v327.blend"
WARDROBE = ROOT / "production_v325_wardrobe_foundation" / "Character_An_wardrobe_foundation_v325.blend"
STAGE = ROOT / "production_v328_identity_seam_hair"
OUTPUT = STAGE / "Character_An_identity_seam_hair_v328.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit" / "v328_identity_seam_hair.json"
HEAD = "V326_PHOTOREAL_FACEBUILDER_HEAD"
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


def correct_head_color(head):
    corrected = []
    for material in head.data.materials:
        if not material or not material.node_tree:
            continue
        nodes = material.node_tree.nodes
        links = material.node_tree.links
        image = next((node for node in nodes if node.type == "TEX_IMAGE"), None)
        principled = next((node for node in nodes if node.type == "BSDF_PRINCLED"), None)
        if principled is None:
            principled = next((node for node in nodes if node.type == "BSDF_PRINCIPLED"), None)
        if not image or not principled:
            continue
        for link in list(links):
            if link.to_node == principled and link.to_socket.name == "Base Color":
                links.remove(link)
        hue = nodes.new("ShaderNodeHueSaturation")
        hue.name = "V328_REFERENCE_SKIN_GRADE"
        hue.inputs["Saturation"].default_value = 1.10
        hue.inputs["Value"].default_value = 0.61
        hue.inputs["Fac"].default_value = 1.0
        links.new(image.outputs["Color"], hue.inputs["Color"])
        links.new(hue.outputs["Color"], principled.inputs["Base Color"])
        corrected.append(material.name)
    return corrected


def append_wardrobe():
    names = ["V325_FLORAL_SHIRT", "V325_TROUSERS", "V325_SHIRT_COLLAR_L", "V325_SHIRT_COLLAR_R"]
    with bpy.data.libraries.load(str(WARDROBE), link=False) as (source, target):
        target.objects = [name for name in names if name in source.objects]
    appended = []
    for obj in target.objects:
        if obj is None:
            continue
        bpy.context.scene.collection.objects.link(obj)
        appended.append(obj.name)
    return appended


def hair_material():
    material = bpy.data.materials.new("V328_NATURAL_BLACK_HAIR")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    principled = nodes.get("Principled BSDF")
    principled.inputs["Base Color"].default_value = (0.0020, 0.0025, 0.0035, 1.0)
    principled.inputs["Roughness"].default_value = 0.36
    principled.inputs["Metallic"].default_value = 0.0
    return material


def make_scalp_cap(material, rig):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=64, location=(0.0, -0.069, 1.733))
    cap = bpy.context.object
    cap.name = "V328_DARK_SCALP_CAP"
    cap.scale = (0.089, 0.100, 0.075)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    mesh = cap.data
    remove = [vertex.index for vertex in mesh.vertices if (cap.matrix_world @ vertex.co).z < 1.748]
    group = cap.vertex_groups.new(name="V328_CAP_REMOVE")
    group.add(remove, 1.0, "REPLACE")
    modifier = cap.modifiers.new("V328_KEEP_CAP", "MASK")
    modifier.vertex_group = group.name
    modifier.invert_vertex_group = True
    bevel = cap.modifiers.new("V328_CAP_SMOOTH", "SUBSURF")
    bevel.levels = 1
    bevel.render_levels = 1
    cap.data.materials.append(material)
    cap.parent = rig
    cap.parent_type = "BONE"
    cap.parent_bone = "head"
    return cap


def make_curls(material, rig):
    random.seed(328)
    curve = bpy.data.curves.new("V328_COMPACT_CURL_CURVES", "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 1
    curve.bevel_depth = 0.00125
    curve.bevel_resolution = 2
    curve.resolution_u = 2
    center = Vector((0.0, -0.069, 1.733))
    count = 0
    for ring in range(4, 16):
        phi = ring / 16.0 * 1.04
        around = max(12, int(8 + 28 * math.sin(phi)))
        for index in range(around):
            theta = 2.0 * math.pi * (index / around + random.uniform(-0.018, 0.018))
            root = center + Vector((
                0.092 * math.sin(phi) * math.cos(theta),
                0.104 * math.sin(phi) * math.sin(theta),
                0.078 * math.cos(phi),
            ))
            normal = Vector((
                (root.x - center.x) / 0.092,
                (root.y - center.y) / 0.104,
                (root.z - center.z) / 0.078,
            )).normalized()
            tangent = normal.cross(Vector((0.0, 0.0, 1.0)))
            if tangent.length < 0.1:
                tangent = Vector((1.0, 0.0, 0.0))
            tangent.normalize()
            bitangent = normal.cross(tangent).normalized()
            radius = random.uniform(0.0038, 0.0062)
            spline = curve.splines.new("POLY")
            points = 18
            spline.points.add(points - 1)
            phase = random.random() * math.tau
            for step in range(points):
                t = step / (points - 1)
                angle = phase + t * math.tau * random.uniform(1.15, 1.65)
                point = root + normal * (0.002 + 0.006 * t) + tangent * (radius * math.cos(angle)) + bitangent * (radius * math.sin(angle))
                spline.points[step].co = (*point, 1.0)
            count += 1
    obj = bpy.data.objects.new("V328_COMPACT_NATURAL_CURL_GROOM", curve)
    bpy.context.scene.collection.objects.link(obj)
    curve.materials.append(material)
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = "head"
    return obj, count


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    for folder in (STAGE, RENDERS, AUDIT.parent):
        folder.mkdir(parents=True, exist_ok=True)
    legacy = bpy.data.objects.get("V217_TIGHT_CURL_GROOM")
    if legacy:
        bpy.data.objects.remove(legacy, do_unlink=True)
    head = bpy.data.objects[HEAD]
    rig = bpy.data.objects[RIG]
    corrected = correct_head_color(head)
    wardrobe = append_wardrobe()
    material = hair_material()
    cap = make_scalp_cap(material, rig)
    curls, curl_count = make_curls(material, rig)
    scene = bpy.context.scene
    scene["V328_STATUS"] = "IDENTITY_JOIN_AND_GROOM_REBUILT_VISUAL_REVIEW_REQUIRED"
    scene["V328_CURL_COUNT"] = curl_count
    camera = bpy.data.objects["V323_CAMERA"]
    target = Vector((0.0, -0.065, 1.665))
    renders = {
        "portrait_front": render(scene, camera, RENDERS / "v328_portrait_front.png", Vector((0.0, -1.28, 1.67)), target, 104.0, (900, 900)),
        "portrait_three_quarter": render(scene, camera, RENDERS / "v328_portrait_three_quarter.png", Vector((0.58, -1.16, 1.70)), target, 100.0, (900, 900)),
        "portrait_profile": render(scene, camera, RENDERS / "v328_portrait_profile.png", Vector((1.22, -0.03, 1.67)), target, 100.0, (900, 900)),
        "full_front": render(scene, camera, RENDERS / "v328_full_front.png", Vector((0.0, -3.55, 1.02)), Vector((0.0, 0.0, 1.0)), 68.0, (900, 1100)),
    }
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v328-identity-seam-hair-v1",
        "status": "BUILT_VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)},
        "wardrobe_source": {"path": str(WARDROBE.relative_to(ROOT)), "sha256": sha(WARDROBE)},
        "head_color_materials": corrected,
        "legacy_groom_removed": legacy is not None,
        "wardrobe_objects": wardrobe,
        "hair": {"cap": cap.name, "curls": curls.name, "curl_count": curl_count},
        "renders": renders,
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha(OUTPUT)},
    }
    AUDIT.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V328_IDENTITY_SEAM_HAIR_OK=" + json.dumps(record["output"], sort_keys=True))


if __name__ == "__main__":
    main()
