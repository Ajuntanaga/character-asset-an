"""Use the complete FaceBuilder head and remove the duplicate generic head/jaw."""

from pathlib import Path
import hashlib
import json

import bpy
from mathutils import Vector

ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v330_intact_head_underlay" / "Character_An_intact_head_underlay_v330.blend"
STAGE = ROOT / "production_v331_uncut_facebuilder_head"
OUTPUT = STAGE / "Character_An_uncut_facebuilder_head_v331.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit" / "v331_uncut_facebuilder_head.json"

def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1048576), b""):
            h.update(block)
    return h.hexdigest()

def aim(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()

def render(scene, camera, path, location, target, lens):
    camera.location = location
    camera.data.lens = lens
    aim(camera, target)
    scene.camera = camera
    scene.render.resolution_x = scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(path)}

def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    for folder in (STAGE, RENDERS, AUDIT.parent):
        folder.mkdir(parents=True, exist_ok=True)
    head = bpy.data.objects["V326_PHOTOREAL_FACEBUILDER_HEAD"]
    body = bpy.data.objects["V322_MB_MALE_BODY"]
    for modifier in list(head.modifiers):
        if modifier.type == "MASK" and "HEAD" in modifier.name:
            head.modifiers.remove(modifier)
    old = body.modifiers.get("V327_KEEP_BODY")
    if old:
        body.modifiers.remove(old)
    group = body.vertex_groups.new(name="V331_BODY_ABOVE_NECK")
    indices = [v.index for v in body.data.vertices if (body.matrix_world @ v.co).z > 1.592]
    group.add(indices, 1.0, "REPLACE")
    modifier = body.modifiers.new("V331_KEEP_BODY", "MASK")
    modifier.vertex_group = group.name
    modifier.invert_vertex_group = True
    body.modifiers.move(body.modifiers.find(modifier.name), 0)
    scene = bpy.context.scene
    scene["V331_STATUS"] = "UNCUT_FACEBUILDER_HEAD_VISUAL_REVIEW_REQUIRED"
    camera = bpy.data.objects["V323_CAMERA"]
    target = Vector((0.0, -0.065, 1.665))
    renders = {
        "portrait_front": render(scene, camera, RENDERS / "v331_portrait_front.png", Vector((0.0, -1.28, 1.67)), target, 104.0),
        "portrait_three_quarter": render(scene, camera, RENDERS / "v331_portrait_three_quarter.png", Vector((0.58, -1.16, 1.70)), target, 100.0),
        "portrait_profile": render(scene, camera, RENDERS / "v331_portrait_profile.png", Vector((1.22, -0.03, 1.67)), target, 100.0),
    }
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v331-uncut-facebuilder-head-v1",
        "status": "BUILT_VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)},
        "generic_head_mask_vertices": len(indices),
        "renders": renders,
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha(OUTPUT)},
    }
    AUDIT.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V331_UNCUT_HEAD_OK=" + json.dumps(record["output"], sort_keys=True))

if __name__ == "__main__":
    main()
