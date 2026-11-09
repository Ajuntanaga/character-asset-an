"""Correct V328 neck overlap, garment palette, and groom placement."""

from pathlib import Path
import hashlib
import json

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v328_identity_seam_hair" / "Character_An_identity_seam_hair_v328.blend"
STAGE = ROOT / "production_v329_neck_groom_correction"
OUTPUT = STAGE / "Character_An_neck_groom_correction_v329.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit" / "v329_neck_groom_correction.json"


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


def replace_mask(obj, name, group_name, cutoff, keep_above):
    old = obj.modifiers.get(name)
    if old:
        obj.modifiers.remove(old)
    group = obj.vertex_groups.get(group_name) or obj.vertex_groups.new(name=group_name)
    vertices = [v.index for v in obj.data.vertices if (obj.matrix_world @ v.co).z > cutoff]
    if vertices:
        group.add(vertices, 1.0, "REPLACE")
    modifier = obj.modifiers.new(name, "MASK")
    modifier.vertex_group = group.name
    modifier.invert_vertex_group = not keep_above
    obj.modifiers.move(obj.modifiers.find(modifier.name), 0)
    return len(vertices)


def darken_head():
    node = bpy.data.materials["FBHead_preview_mat"].node_tree.nodes.get("V328_REFERENCE_SKIN_GRADE")
    if node:
        node.inputs["Value"].default_value = 0.46
        node.inputs["Saturation"].default_value = 1.16


def darken_shirt():
    shirt = bpy.data.objects.get("V325_FLORAL_SHIRT")
    if not shirt:
        return None
    for material in shirt.data.materials:
        if not material or not material.node_tree:
            continue
        principled = next((n for n in material.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
        image = next((n for n in material.node_tree.nodes if n.type == "TEX_IMAGE"), None)
        if principled and image:
            for link in list(material.node_tree.links):
                if link.to_node == principled and link.to_socket.name == "Base Color":
                    material.node_tree.links.remove(link)
            mix = material.node_tree.nodes.new("ShaderNodeMixRGB")
            mix.name = "V329_DARK_FLORAL_GRADE"
            mix.blend_type = "MULTIPLY"
            mix.inputs[0].default_value = 1.0
            mix.inputs[2].default_value = (0.065, 0.075, 0.085, 1.0)
            material.node_tree.links.new(image.outputs["Color"], mix.inputs[1])
            material.node_tree.links.new(mix.outputs["Color"], principled.inputs["Base Color"])
            principled.inputs["Roughness"].default_value = 0.58
    return shirt.name


def repair_groom_placement():
    repaired = []
    for name in ("V328_DARK_SCALP_CAP", "V328_COMPACT_NATURAL_CURL_GROOM"):
        obj = bpy.data.objects.get(name)
        if not obj:
            continue
        obj.parent = None
        obj.matrix_parent_inverse.identity()
        obj.matrix_world.identity()
        if name == "V328_DARK_SCALP_CAP":
            obj.location = (0.0, -0.069, 1.733)
        repaired.append(name)
    return repaired


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    for folder in (STAGE, RENDERS, AUDIT.parent):
        folder.mkdir(parents=True, exist_ok=True)
    for name in ("V325_SHIRT_COLLAR_L", "V325_SHIRT_COLLAR_R"):
        obj = bpy.data.objects.get(name)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)
    body = bpy.data.objects["V322_MB_MALE_BODY"]
    head = bpy.data.objects["V326_PHOTOREAL_FACEBUILDER_HEAD"]
    body_count = replace_mask(body, "V327_KEEP_BODY", "V329_BODY_ABOVE_NECK", 1.623, False)
    head_count = replace_mask(head, "V327_KEEP_HEAD", "V329_HEAD_ABOVE_NECK", 1.603, True)
    darken_head()
    shirt = darken_shirt()
    groom = repair_groom_placement()
    scene = bpy.context.scene
    scene["V329_STATUS"] = "NECK_GROOM_CORRECTED_VISUAL_REVIEW_REQUIRED"
    camera = bpy.data.objects["V323_CAMERA"]
    target = Vector((0.0, -0.065, 1.665))
    renders = {
        "portrait_front": render(scene, camera, RENDERS / "v329_portrait_front.png", Vector((0.0, -1.28, 1.67)), target, 104.0, (900, 900)),
        "portrait_three_quarter": render(scene, camera, RENDERS / "v329_portrait_three_quarter.png", Vector((0.58, -1.16, 1.70)), target, 100.0, (900, 900)),
        "portrait_profile": render(scene, camera, RENDERS / "v329_portrait_profile.png", Vector((1.22, -0.03, 1.67)), target, 100.0, (900, 900)),
        "full_front": render(scene, camera, RENDERS / "v329_full_front.png", Vector((0.0, -3.55, 1.02)), Vector((0.0, 0.0, 1.0)), 68.0, (900, 1100)),
    }
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v329-neck-groom-correction-v1",
        "status": "BUILT_VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)},
        "body_overlap_vertices": body_count,
        "head_kept_vertices": head_count,
        "shirt": shirt,
        "groom_repaired": groom,
        "renders": renders,
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha(OUTPUT)},
    }
    AUDIT.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V329_NECK_GROOM_OK=" + json.dumps(record["output"], sort_keys=True))


if __name__ == "__main__":
    main()
