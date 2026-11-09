"""Test native Rigify automatic weights on the untouched V211 production body."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v211_clean_base" / "Character_An_clean_base_v211.blend"
STAGE = ROOT / "production_v239_clean_auto_rig"
OUTPUT = STAGE / "Character_An_clean_auto_rig_v239.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def mapped_point(name: str, point: Vector) -> Vector:
    x, y, z = point
    body_bones = {
        "spine", "spine.001", "spine.002", "spine.003", "spine.004", "spine.005", "spine.006",
        "pelvis.L", "pelvis.R", "breast.L", "breast.R", "thigh.L", "thigh.R", "shin.L", "shin.R",
        "foot.L", "foot.R", "toe.L", "toe.R", "heel.02.L", "heel.02.R",
    }
    if "shoulder." in name:
        side = -1.0 if x < 0.0 else 1.0
        absolute = abs(x)
        if absolute <= 0.195:
            nx = absolute * (0.170 / 0.195)
        else:
            nx = 0.170 + (min(absolute, 0.789) - 0.195) / (0.789 - 0.195) * (0.452 - 0.170)
        return Vector((side * nx, y * 0.75, z * 0.91))
    if any(token in name for token in ("upper_arm.", "forearm.")):
        # Fit the stock Rigify arm centerline to the V211 downward A-pose.
        # The previous uniform z scale left the wrists ~13 cm above the mesh.
        side = -1.0 if x < 0.0 else 1.0
        absolute = abs(x)
        keys = (
            (0.1953, 0.180, 1.450),
            (0.4424, 0.292, 1.275),
            (0.6594, 0.352, 1.055),
        )
        if absolute <= keys[1][0]:
            first, second = keys[0], keys[1]
        else:
            first, second = keys[1], keys[2]
        factor = max(0.0, min(1.0, (absolute - first[0]) / (second[0] - first[0])))
        nx = first[1] + factor * (second[1] - first[1])
        nz = first[2] + factor * (second[2] - first[2])
        return Vector((side * nx, y * 0.35, nz))
    if any(token in name for token in ("hand.", "palm.", "f_index.", "f_middle.", "f_ring.", "f_pinky.", "thumb.")):
        # Preserve the stock hand's internal topology with one local affine
        # transform about the wrist. This keeps all connected finger joints
        # ordered while seating the fingertips inside the V211 neutral mesh.
        side = -1.0 if x < 0.0 else 1.0
        absolute = abs(x)
        nx = 0.352 + (absolute - 0.6594) * 0.75
        ny = (y - 0.0492) * 1.15
        nz = 1.055 + (z - 1.3061) * 1.30
        return Vector((side * nx, ny, nz))
    if name in body_bones:
        return Vector((x * 0.95, y * 0.78, z * 0.91))
    return Vector((x * 0.83, y * 0.90, 1.505 + (z - 1.720) * 1.135))


def activate(obj: bpy.types.Object) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def render(scene: bpy.types.Scene, camera_name: str, path: Path) -> None:
    scene.camera = bpy.data.objects[camera_name]
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def main() -> None:
    STAGE.mkdir(parents=True, exist_ok=True)
    RENDERS.mkdir(parents=True, exist_ok=True)
    AUDIT.mkdir(parents=True, exist_ok=True)
    if Path(bpy.data.filepath).resolve() != SOURCE.resolve():
        raise RuntimeError(f"Open the V211 source in a separate MCP call first: {SOURCE}")
    bpy.ops.preferences.addon_enable(module="rigify")

    body = bpy.data.objects["V211_BODY_NEUTRAL"]
    world = body.matrix_world.copy()
    body.parent = None
    body.matrix_world = world
    activate(body)
    with bpy.context.temp_override(
        active_object=body, object=body, selected_objects=[body], selected_editable_objects=[body]
    ):
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    # Construct the stock human metarig directly. Rigify's menu operator reads
    # context.active_object after opening a file, but MCP's execution context
    # intentionally omits that key.
    from rigify.metarigs import human as human_metarig

    metarig_data = bpy.data.armatures.new("V239_METARIG_DATA")
    metarig = bpy.data.objects.new("V239_METARIG", metarig_data)
    bpy.context.scene.collection.objects.link(metarig)
    activate(metarig)
    with bpy.context.temp_override(
        active_object=metarig, object=metarig, selected_objects=[metarig], selected_editable_objects=[metarig]
    ):
        bpy.ops.object.mode_set(mode="EDIT")
        human_metarig.create(metarig)
        bpy.ops.object.mode_set(mode="OBJECT")
    metarig.name = "V239_METARIG"
    activate(metarig)
    with bpy.context.temp_override(
        active_object=metarig, object=metarig, selected_objects=[metarig], selected_editable_objects=[metarig]
    ):
        bpy.ops.object.mode_set(mode="EDIT")
        # Connected edit bones share endpoint storage. Mapping them in-place
        # causes a child head to transform an already-transformed parent tail,
        # catastrophically folding the finger chains. Transform the immutable
        # stock coordinates instead so every shared joint is mapped once.
        stock_points = {
            bone.name: (bone.head.copy(), bone.tail.copy())
            for bone in metarig.data.edit_bones
        }
        for bone in metarig.data.edit_bones:
            stock_head, stock_tail = stock_points[bone.name]
            bone.head = mapped_point(bone.name, stock_head)
            bone.tail = mapped_point(bone.name, stock_tail)
        bpy.ops.object.mode_set(mode="OBJECT")
    metarig.data.rigify_rig_basename = "V239_CLEAN_CHARACTER_RIG"
    activate(metarig)
    bpy.ops.pose.rigify_generate()
    rig = bpy.context.active_object
    if rig is None or rig.type != "ARMATURE":
        raise RuntimeError("Rigify failed to generate V239 rig")
    rig.name = "V239_CLEAN_CHARACTER_RIG"
    metarig.hide_viewport = True
    metarig.hide_render = True

    deform_prefixes = (
        "DEF-spine", "DEF-shoulder", "DEF-upper_arm", "DEF-forearm", "DEF-hand", "DEF-palm",
        "DEF-f_", "DEF-thumb", "DEF-thigh", "DEF-shin", "DEF-foot", "DEF-toe", "DEF-pelvis", "DEF-breast",
    )
    for bone in rig.data.bones:
        if bone.use_deform and not bone.name.startswith(deform_prefixes):
            bone.use_deform = False

    # Native bone-heat weights are tested on the untouched, well-separated A
    # pose. V214 replaced this step with a deterministic nearest-segment field;
    # this stage deliberately restores the standard weighting path.
    activate(body)
    rig.select_set(True)
    bpy.context.view_layer.objects.active = rig
    with bpy.context.temp_override(
        active_object=rig, object=rig, selected_objects=[body, rig], selected_editable_objects=[body, rig]
    ):
        bpy.ops.object.parent_set(type="ARMATURE_AUTO")
    armature = next((modifier for modifier in body.modifiers if modifier.type == "ARMATURE"), None)
    if armature is None:
        raise RuntimeError("Automatic weights did not create an armature modifier")
    armature.name = "V239_AUTO_WEIGHT_ARMATURE"
    armature.use_deform_preserve_volume = True

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 720
    scene.render.resolution_y = 960
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.frame_start = 1
    scene.frame_end = 20
    scene.frame_set(1)
    render(scene, "CAM_V211_FRONT", RENDERS / "v239_neutral_front.png")

    pose = {
        "upper_arm_fk.L": (math.radians(-10), math.radians(-8), math.radians(-22)),
        "forearm_fk.L": (0.0, math.radians(-10), math.radians(-58)),
        "upper_arm_fk.R": (math.radians(-8), math.radians(10), math.radians(18)),
        "forearm_fk.R": (0.0, math.radians(8), math.radians(48)),
        "thigh_fk.L": (math.radians(6), 0.0, math.radians(-4)),
        "shin_fk.L": (math.radians(-12), 0.0, 0.0),
        "spine_fk.002": (0.0, math.radians(5), math.radians(-4)),
    }
    for name, rotation in pose.items():
        control = rig.pose.bones.get(name)
        if control:
            control.rotation_mode = "XYZ"
            control.rotation_euler = rotation
    bpy.context.view_layer.update()
    render(scene, "CAM_V211_FRONT", RENDERS / "v239_pose_front.png")
    render(scene, "CAM_V211_FRONT_LEFT_3Q", RENDERS / "v239_pose_three_quarter.png")

    scene["V239_STATUS"] = "CLEAN_V211_NATIVE_AUTO_WEIGHTS_TEST"
    scene["V239_WEIGHTING"] = "Blender native armature automatic weights on untouched V211 A-pose"
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v239-clean-auto-rig-v1",
        "status": "BUILT_VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha256(SOURCE)},
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha256(OUTPUT)},
        "body": body.name,
        "rig": rig.name,
        "generated_bones": len(rig.data.bones),
        "deform_bones": sum(1 for bone in rig.data.bones if bone.use_deform),
        "vertex_groups": len(body.vertex_groups),
        "armature_modifier": armature.name,
        "renders": sorted(str(path.relative_to(ROOT)) for path in RENDERS.glob("*.png")),
    }
    (AUDIT / "v239_manifest.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("V239_CLEAN_AUTO_RIG_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
