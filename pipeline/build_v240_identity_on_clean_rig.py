"""Attach the accepted V221 identity assembly to the stable V239 clean rig."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v239_clean_auto_rig" / "Character_An_clean_auto_rig_v239.blend"
IDENTITY = ROOT / "production_v221_identity_cleanup" / "Character_An_identity_cleanup_v221.blend"
STAGE = ROOT / "production_v240_identity_clean_rig"
OUTPUT = STAGE / "Character_An_identity_clean_rig_v240.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"

ASSEMBLY = [
    "V216_REFERENCE_FITTED_HEAD",
    "V216_EYE_L", "V216_EYE_R",
    "V216_IRIS_L", "V216_IRIS_R",
    "V216_PUPIL_L", "V216_PUPIL_R",
    "V217_TIGHT_CURL_GROOM", "V217_CURL_CLUSTERS",
    "V217_BROWS", "V217_BEARD_STUBBLE",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def point_at(obj: bpy.types.Object, target: Vector) -> None:
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(scene: bpy.types.Scene, camera: bpy.types.Object, path: Path, location: Vector, target: Vector, lens: float, resolution: tuple[int, int]) -> None:
    camera.location = location
    camera.data.lens = lens
    point_at(camera, target)
    scene.camera = camera
    scene.render.resolution_x, scene.render.resolution_y = resolution
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def main() -> None:
    if Path(bpy.data.filepath).resolve() != SOURCE.resolve():
        raise RuntimeError(f"Open V239 in a separate MCP call first: {SOURCE}")
    STAGE.mkdir(parents=True, exist_ok=True)
    RENDERS.mkdir(parents=True, exist_ok=True)
    AUDIT.mkdir(parents=True, exist_ok=True)

    rig = bpy.data.objects["V239_CLEAN_CHARACTER_RIG"]
    body = bpy.data.objects["V211_BODY_NEUTRAL"]
    for pose_bone in rig.pose.bones:
        pose_bone.location = (0.0, 0.0, 0.0)
        pose_bone.rotation_quaternion = (1.0, 0.0, 0.0, 0.0)
        pose_bone.rotation_euler = (0.0, 0.0, 0.0)
        pose_bone.scale = (1.0, 1.0, 1.0)
    bpy.context.view_layer.update()

    # Retain the clean body topology while suppressing its generic head above
    # the collar line. The FaceBuilder head carries the accepted identity.
    keep = body.vertex_groups.get("V240_BODY_KEEP") or body.vertex_groups.new(name="V240_BODY_KEEP")
    keep_indices = [
        vertex.index
        for vertex in body.data.vertices
        if (body.matrix_world @ vertex.co).z <= 1.475
    ]
    keep.add(keep_indices, 1.0, "REPLACE")
    mask = body.modifiers.get("V240_GENERIC_HEAD_MASK") or body.modifiers.new("V240_GENERIC_HEAD_MASK", "MASK")
    mask.vertex_group = keep.name
    mask.invert_vertex_group = False

    for name in ("V211_EYE_L", "V211_EYE_R"):
        eye = bpy.data.objects.get(name)
        if eye:
            eye.hide_render = True
            eye.hide_viewport = True

    with bpy.data.libraries.load(str(IDENTITY), link=False) as (source, target):
        missing = [name for name in ASSEMBLY if name not in source.objects]
        if missing:
            raise RuntimeError(f"V221 identity objects missing: {missing}")
        target.objects = ASSEMBLY
    appended = []
    for obj in target.objects:
        if obj is None:
            continue
        bpy.context.scene.collection.objects.link(obj)
        appended.append(obj)
    bpy.context.view_layer.update()

    attached = []
    for obj in appended:
        # V221 objects are unparented. matrix_local preserves their authored
        # source transform immediately after library append; matrix_world can
        # remain stale until a depsgraph evaluation and previously expanded the
        # 0.136-scale FaceBuilder head to unit scale.
        source_world = obj.matrix_local.copy()
        obj.parent = rig
        obj.parent_type = "BONE"
        obj.parent_bone = "head"
        obj.matrix_world = source_world
        attached.append(obj.name)

    for name in ("V217_BROWS", "V217_BEARD_STUBBLE"):
        obj = bpy.data.objects.get(name)
        if obj:
            obj.hide_render = True
            obj.hide_viewport = True

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.view_settings.look = "AgX - Medium High Contrast"
    camera = bpy.data.objects["CAM_V211_FRONT"]

    head = rig.pose.bones["head"]
    head.rotation_mode = "XYZ"
    head.rotation_euler = (0.0, 0.0, 0.0)
    bpy.context.view_layer.update()
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 2.08
    render(scene, camera, RENDERS / "v240_full_front.png", Vector((0.0, -4.2, 0.92)), Vector((0.0, 0.0, 0.92)), 70.0, (800, 1050))
    camera.data.type = "PERSP"
    render(scene, camera, RENDERS / "v240_identity_front.png", Vector((0.0, -1.45, 1.60)), Vector((0.0, 0.0, 1.58)), 82.0, (900, 900))

    head.rotation_euler.y = math.radians(-18.0)
    bpy.context.view_layer.update()
    render(scene, camera, RENDERS / "v240_head_turn_left.png", Vector((0.0, -1.45, 1.60)), Vector((0.0, 0.0, 1.58)), 82.0, (900, 900))
    head.rotation_euler.y = math.radians(18.0)
    bpy.context.view_layer.update()
    render(scene, camera, RENDERS / "v240_head_turn_right.png", Vector((0.0, -1.45, 1.60)), Vector((0.0, 0.0, 1.58)), 82.0, (900, 900))
    head.rotation_euler.y = 0.0
    bpy.context.view_layer.update()

    scene["V240_STATUS"] = "V221_IDENTITY_ATTACHED_TO_STABLE_V239_RIG"
    scene["V240_ATTACHED_OBJECTS"] = ",".join(attached)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v240-identity-clean-rig-v1",
        "status": "BUILT_VISUAL_REVIEW_REQUIRED",
        "source_rig": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha256(SOURCE)},
        "source_identity": {"path": str(IDENTITY.relative_to(ROOT)), "sha256": sha256(IDENTITY)},
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha256(OUTPUT)},
        "attached": attached,
        "generic_head_mask_vertex_count": len(keep_indices),
        "renders": sorted(str(path.relative_to(ROOT)) for path in RENDERS.glob("*.png")),
    }
    (AUDIT / "v240_manifest.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("V240_IDENTITY_CLEAN_RIG_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
