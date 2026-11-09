"""Restore the intact FaceBuilder head and use the body neck only as an underlay."""

from pathlib import Path
import hashlib
import json

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v329_neck_groom_correction" / "Character_An_neck_groom_correction_v329.blend"
STAGE = ROOT / "production_v330_intact_head_underlay"
OUTPUT = STAGE / "Character_An_intact_head_underlay_v330.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit" / "v330_intact_head_underlay.json"


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


def set_mask(obj, modifier_name, group_name, cutoff, keep_above):
    old = obj.modifiers.get(modifier_name)
    if old:
        obj.modifiers.remove(old)
    group = obj.vertex_groups.get(group_name) or obj.vertex_groups.new(name=group_name)
    indices = [v.index for v in obj.data.vertices if (obj.matrix_world @ v.co).z > cutoff]
    if indices:
        group.add(indices, 1.0, "REPLACE")
    modifier = obj.modifiers.new(modifier_name, "MASK")
    modifier.vertex_group = group.name
    modifier.invert_vertex_group = not keep_above
    obj.modifiers.move(obj.modifiers.find(modifier.name), 0)
    return len(indices)


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    for folder in (STAGE, RENDERS, AUDIT.parent):
        folder.mkdir(parents=True, exist_ok=True)
    for name in ("V328_DARK_SCALP_CAP", "V328_COMPACT_NATURAL_CURL_GROOM"):
        obj = bpy.data.objects.get(name)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)
    head = bpy.data.objects["V326_PHOTOREAL_FACEBUILDER_HEAD"]
    body = bpy.data.objects["V322_MB_MALE_BODY"]
    head_count = set_mask(head, "V327_KEEP_HEAD", "V330_HEAD_ABOVE_NECK", 1.574, True)
    body_count = set_mask(body, "V327_KEEP_BODY", "V330_BODY_ABOVE_NECK", 1.610, False)
    material = bpy.data.materials.get("FBHead_preview_mat")
    if material and material.node_tree:
        grade = material.node_tree.nodes.get("V328_REFERENCE_SKIN_GRADE")
        if grade:
            grade.inputs["Value"].default_value = 0.37
            grade.inputs["Saturation"].default_value = 0.92
    scene = bpy.context.scene
    scene["V330_STATUS"] = "INTACT_HEAD_WITH_NECK_UNDERLAY_VISUAL_REVIEW_REQUIRED"
    camera = bpy.data.objects["V323_CAMERA"]
    target = Vector((0.0, -0.065, 1.665))
    renders = {
        "portrait_front": render(scene, camera, RENDERS / "v330_portrait_front.png", Vector((0.0, -1.28, 1.67)), target, 104.0, (900, 900)),
        "portrait_three_quarter": render(scene, camera, RENDERS / "v330_portrait_three_quarter.png", Vector((0.58, -1.16, 1.70)), target, 100.0, (900, 900)),
        "portrait_profile": render(scene, camera, RENDERS / "v330_portrait_profile.png", Vector((1.22, -0.03, 1.67)), target, 100.0, (900, 900)),
        "full_front": render(scene, camera, RENDERS / "v330_full_front.png", Vector((0.0, -3.55, 1.02)), Vector((0.0, 0.0, 1.0)), 68.0, (900, 1100)),
    }
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v330-intact-head-underlay-v1",
        "status": "BUILT_VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)},
        "head_kept_vertices": head_count,
        "body_underlay_vertices": body_count,
        "failed_procedural_groom_removed": True,
        "renders": renders,
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha(OUTPUT)},
    }
    AUDIT.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V330_INTACT_HEAD_OK=" + json.dumps(record["output"], sort_keys=True))


if __name__ == "__main__":
    main()
