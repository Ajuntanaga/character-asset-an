"""Repair the deterministic upper-arm/forearm weights exposed by the guitar IK pose."""

from pathlib import Path
import math

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
BASE = ROOT / "production_v228_garment_rig_coupling" / "Character_An_garment_rig_v228.blend"
OUT = ROOT / "production_v229_arm_weight_repair"
RENDERS = OUT / "renders"
OUTPUT = OUT / "Character_An_arm_weights_v229.blend"
RENDERS.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(BASE))

rig = bpy.data.objects["V214_CHARACTER_RIG"]


def point_segment_distance(point, start, end):
    segment = end - start
    denom = segment.length_squared
    if denom <= 1e-12:
        return (point - start).length
    factor = max(0.0, min(1.0, (point - start).dot(segment) / denom))
    return (point - (start + segment * factor)).length


def repair_object(obj):
    repaired = 0
    for vertex in obj.data.vertices:
        point = vertex.co
        ax = abs(point.x)
        # Upper/forearm shaft only. Preserve torso and articulated hand/finger weights.
        if not (0.135 < ax < 0.305 and 1.025 < point.z < 1.475):
            continue
        side = "L" if point.x > 0.0 else "R"
        candidates = [
            f"DEF-upper_arm.{side}",
            f"DEF-upper_arm.{side}.001",
            f"DEF-forearm.{side}",
            f"DEF-forearm.{side}.001",
            f"DEF-hand.{side}",
        ]
        scored = []
        for name in candidates:
            bone = rig.data.bones.get(name)
            if bone is None:
                continue
            distance = point_segment_distance(point, bone.head_local, bone.tail_local)
            scored.append((distance, name))
        scored.sort(key=lambda item: item[0])
        selected = scored[:2]
        if not selected:
            continue
        for group in obj.vertex_groups:
            try:
                group.remove([vertex.index])
            except RuntimeError:
                pass
        raw = [(math.exp(-distance * 70.0), name) for distance, name in selected]
        total = sum(weight for weight, _name in raw)
        for weight, name in raw:
            group = obj.vertex_groups.get(name) or obj.vertex_groups.new(name=name)
            group.add([vertex.index], weight / total, "REPLACE")
        repaired += 1
    return repaired


repaired = {}
for name in ("V216_BODY_WITH_NECK_STUB", "V219_FITTED_SHIRT", "V219_OPEN_JACKET"):
    repaired[name] = repair_object(bpy.data.objects[name])

camera = bpy.data.objects["V219_CAMERA"]


def point_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


scene = bpy.context.scene
scene.frame_set(1)
scene.camera = camera
scene.render.engine = "BLENDER_EEVEE"
scene.render.image_settings.file_format = "PNG"
views = {
    "full_front": (Vector((0.0, -4.2, 1.02)), Vector((0.0, 0.0, 0.95)), 58.0, (900, 1100)),
    "performance": (Vector((0.0, -2.55, 1.16)), Vector((-0.05, -0.02, 1.06)), 70.0, (1100, 900)),
}
for name, (location, target, lens, resolution) in views.items():
    camera.location = location
    camera.data.lens = lens
    point_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = resolution
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(RENDERS / f"v229_{name}.png")
    bpy.ops.render.render(write_still=True)

scene["V229_STATUS"] = "GATED_ARM_WEIGHT_FIELD_REPAIR_CANDIDATE"
scene["V229_REPAIRED_VERTICES"] = str(repaired)
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
print({"status": "ok", "output": str(OUTPUT), "repaired": repaired})
