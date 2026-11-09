from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v212_identity/Character_An_identity_v212.blend"
STAGE = ROOT / "production_v214_rig"
OUTPUT = STAGE / "Character_An_rig_v214.blend"
RENDER_DIR = STAGE / "renders/deformation"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def mapped_point(name: str, point: Vector) -> Vector:
    x, y, z = point
    body_bones = {
        "spine", "spine.001", "spine.002", "spine.003", "spine.004", "spine.005", "spine.006",
        "pelvis.L", "pelvis.R", "breast.L", "breast.R",
        "thigh.L", "thigh.R", "shin.L", "shin.R", "foot.L", "foot.R", "toe.L", "toe.R",
        "heel.02.L", "heel.02.R",
    }
    arm = any(token in name for token in ("shoulder.", "upper_arm.", "forearm.", "hand.", "palm.", "f_index.", "f_middle.", "f_ring.", "f_pinky.", "thumb."))
    if arm:
        side = -1.0 if x < 0.0 else 1.0
        absolute = abs(x)
        if absolute <= 0.195:
            nx = absolute * (0.170 / 0.195)
        else:
            nx = 0.170 + (min(absolute, 0.789) - 0.195) / (0.789 - 0.195) * (0.452 - 0.170)
        return Vector((side * nx, y * 0.75, z * 0.91))
    if name in body_bones:
        return Vector((x * 0.95, y * 0.78, z * 0.91))
    # Facial controls are fitted to the compact V212 head independently of
    # the torso scaling. They remain a provisional Rigify interface until the
    # FaceBuilder head and its FACS shapes are conformed.
    return Vector((x * 0.83, y * 0.90, 1.505 + (z - 1.720) * 1.135))


def activate(obj: bpy.types.Object) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def point_segment_distance(point: Vector, start: Vector, end: Vector) -> float:
    segment = end - start
    denominator = segment.length_squared
    if denominator <= 1e-12:
        return (point - start).length
    t = max(0.0, min(1.0, (point - start).dot(segment) / denominator))
    return (point - (start + segment * t)).length


def assign_regional_weights(body: bpy.types.Object, rig: bpy.types.Object) -> None:
    body.vertex_groups.clear()
    deform = [bone for bone in rig.data.bones if bone.use_deform]
    groups = {bone.name: body.vertex_groups.new(name=bone.name) for bone in deform}
    central = [bone for bone in deform if bone.name.startswith(("DEF-spine", "DEF-pelvis", "DEF-breast"))]
    arms = {
        side: [bone for bone in deform if bone.name.endswith(side) and bone.name.startswith((
            "DEF-shoulder", "DEF-upper_arm", "DEF-forearm", "DEF-hand", "DEF-palm", "DEF-f_", "DEF-thumb"
        ))]
        for side in (".L", ".R")
    }
    legs = {
        side: [bone for bone in deform if bone.name.endswith(side) and bone.name.startswith((
            "DEF-thigh", "DEF-shin", "DEF-foot", "DEF-toe"
        ))]
        for side in (".L", ".R")
    }
    matrix = body.matrix_world
    for vertex in body.data.vertices:
        point = matrix @ vertex.co
        side = ".L" if point.x >= 0.0 else ".R"
        if point.z < 0.98:
            candidates = legs[side] + [bone for bone in central if bone.name.startswith(("DEF-spine", "DEF-pelvis"))]
        elif abs(point.x) > 0.205 and point.z > 0.96:
            candidates = arms[side] + [bone for bone in central if bone.name.startswith("DEF-spine")]
        else:
            candidates = central + [bone for bone in arms[side] if bone.name.startswith("DEF-shoulder")]
        distances = sorted(
            ((point_segment_distance(point, rig.matrix_world @ bone.head_local, rig.matrix_world @ bone.tail_local), bone.name) for bone in candidates),
            key=lambda item: item[0],
        )[:4]
        raw = [(1.0 / max(distance, 0.008) ** 3, name) for distance, name in distances]
        total = sum(weight for weight, _name in raw)
        for weight, name in raw:
            groups[name].add([vertex.index], weight / total, "REPLACE")


for directory in (STAGE, RENDER_DIR, STAGE / "audit"):
    directory.mkdir(parents=True, exist_ok=True)

if Path(bpy.data.filepath).resolve() != SOURCE.resolve():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
bpy.ops.preferences.addon_enable(module="rigify")
body = bpy.data.objects["V212_BODY_IDENTITY"]
body_world = body.matrix_world.copy()
body.parent = None
body.matrix_world = body_world
bpy.context.view_layer.update()

bpy.ops.object.armature_human_metarig_add()
metarig = bpy.context.view_layer.objects.active
metarig.name = "V214_METARIG"
activate(metarig)
bpy.ops.object.mode_set(mode="EDIT")
for bone in metarig.data.edit_bones:
    bone.head = mapped_point(bone.name, bone.head.copy())
    bone.tail = mapped_point(bone.name, bone.tail.copy())
bpy.ops.object.mode_set(mode="OBJECT")
metarig.data.name = "V214_METARIG_DATA"
metarig.data.rigify_rig_basename = "V214_CHARACTER_RIG"

activate(metarig)
bpy.ops.pose.rigify_generate()
rig = bpy.context.view_layer.objects.active
if rig is None or rig.type != "ARMATURE":
    raise RuntimeError("Rigify did not return an armature")
rig.name = "V214_CHARACTER_RIG"
rig.data.name = "V214_CHARACTER_RIG_DATA"
metarig.hide_viewport = True
metarig.hide_render = True

# The V212 body has no internal mouth/teeth topology matching Rigify's facial
# heat map. Let the neck/head chain carry the neutral head; FaceBuilder FACS
# shapes will supply facial deformation after conformation. Leaving these tiny
# facial DEF bones active causes catastrophic heat-weight spikes.
body_deform_prefixes = (
    "DEF-spine", "DEF-shoulder", "DEF-upper_arm", "DEF-forearm", "DEF-hand",
    "DEF-palm", "DEF-f_", "DEF-thumb", "DEF-thigh", "DEF-shin", "DEF-foot",
    "DEF-toe", "DEF-pelvis", "DEF-breast",
)
for bone in rig.data.bones:
    if bone.use_deform and not bone.name.startswith(body_deform_prefixes):
        bone.use_deform = False

# Heat weights crossed the compact A-pose limbs and failed catastrophically in
# pose tests. Use deterministic region-gated nearest-segment weights instead.
assign_regional_weights(body, rig)
armature = body.modifiers.new("V214_ARMATURE", "ARMATURE")
armature.object = rig
armature.use_deform_preserve_volume = True
body_world = body.matrix_world.copy()
body.parent = rig
body.matrix_world = body_world
armature_modifiers = [armature]

action = bpy.data.actions.new("V214_DEFORMATION_MATRIX")
rig.animation_data_create()
rig.animation_data.action = action

controls = {
    "upper_arm_fk.L": (math.radians(-8.0), math.radians(-12.0), math.radians(-24.0)),
    "forearm_fk.L": (0.0, math.radians(-8.0), math.radians(-78.0)),
    "upper_arm_fk.R": (math.radians(-5.0), math.radians(9.0), math.radians(18.0)),
    "forearm_fk.R": (0.0, math.radians(6.0), math.radians(54.0)),
    "spine_fk.002": (0.0, math.radians(7.0), math.radians(-5.0)),
}
for frame in (1, 40):
    for pose_bone in rig.pose.bones:
        pose_bone.rotation_mode = "XYZ"
        pose_bone.rotation_euler = (0.0, 0.0, 0.0)
        pose_bone.keyframe_insert("rotation_euler", frame=frame)
for name, rotation in controls.items():
    pose_bone = rig.pose.bones.get(name)
    if pose_bone is not None:
        pose_bone.rotation_mode = "XYZ"
        pose_bone.rotation_euler = rotation
        pose_bone.keyframe_insert("rotation_euler", frame=20)

scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 40
scene.frame_set(20)
scene["character_asset_stage"] = "V214_RIG_DEFORMATION_CANDIDATE"
scene["rig_source"] = "Rigify human metarig fitted to V212 world landmarks"
scene["face_rig_boundary"] = "provisional until FaceBuilder head/FACS conformation"

scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 720
scene.render.resolution_y = 960
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.camera = bpy.data.objects["CAM_V211_FRONT_LEFT_3Q"]
scene.render.filepath = str(RENDER_DIR / "frame_020_three_quarter.png")
bpy.ops.render.render(write_still=True)
scene.camera = bpy.data.objects["CAM_V211_FRONT"]
scene.render.filepath = str(RENDER_DIR / "frame_020_front.png")
bpy.ops.render.render(write_still=True)
scene.frame_set(1)
scene.render.filepath = str(RENDER_DIR / "frame_001_neutral.png")
bpy.ops.render.render(write_still=True)

bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
record = {
    "stage": "V214_RIG_DEFORMATION_CANDIDATE",
    "source": str(SOURCE.relative_to(ROOT)),
    "source_sha256": sha256(SOURCE),
    "output": str(OUTPUT.relative_to(ROOT)),
    "output_sha256": sha256(OUTPUT),
    "rig": rig.name,
    "generated_bones": len(rig.data.bones),
    "deform_bones": sum(1 for bone in rig.data.bones if bone.use_deform),
    "vertex_groups": len(body.vertex_groups),
    "armature_modifiers": [modifier.name for modifier in armature_modifiers],
    "action": action.name,
    "keyed_controls": sorted(name for name in controls if name in rig.pose.bones),
    "renders": [str(path.relative_to(ROOT)) for path in sorted(RENDER_DIR.glob("*.png"))],
    "status": "structural candidate; deformation renders require visual acceptance",
}
(STAGE / "audit/v214_rig_manifest.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print("V214_RIG_CANDIDATE_BUILT", record)
