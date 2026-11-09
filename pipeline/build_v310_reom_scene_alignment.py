"""Integrate the clean Reom/Rigify body into V300 without replacing accepted assets."""

from pathlib import Path
import hashlib
import json

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v300_guitar_visual_acceptance" / "Character_An_guitar_visual_acceptance_v300.blend"
REOM_SOURCE = ROOT / "production_v307_charmorph_reom_rig" / "Character_An_reom_rig_v307.blend"
STAGE = ROOT / "production_v310_reom_scene_alignment"
OUTPUT = STAGE / "Character_An_reom_scene_alignment_v310.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"


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


def append_reom():
    with bpy.data.libraries.load(str(REOM_SOURCE), link=False) as (source, target):
        required = {"V307_REOM_BODY", "V307_REOM_RIG"}
        missing = required.difference(source.objects)
        if missing:
            raise RuntimeError(f"Missing Reom objects: {sorted(missing)}")
        target.objects = ["V307_REOM_BODY", "V307_REOM_RIG"]
        target.collections = ["WGTS_rig"] if "WGTS_rig" in source.collections else []
    appended = {obj.name: obj for obj in target.objects if obj is not None}
    body = appended["V307_REOM_BODY"]
    rig = appended["V307_REOM_RIG"]
    integration = bpy.data.collections.new("V310_REOM_INTEGRATION")
    bpy.context.scene.collection.children.link(integration)
    for obj in (body, rig):
        if not obj.users_collection:
            integration.objects.link(obj)
        else:
            # Root-scene objects do not retain their original scene membership
            # when appended as standalone objects.
            integration.objects.link(obj)
    for collection in target.collections:
        if collection is not None and collection.name not in bpy.context.scene.collection.children:
            bpy.context.scene.collection.children.link(collection)
            collection.hide_render = True
            collection.hide_viewport = True
    body.name = "V310_REOM_BODY"
    rig.name = "V310_REOM_RIG"
    integration["source_file"] = str(REOM_SOURCE)
    return body, rig, integration


def is_old_character_object(obj, old_rig):
    if obj.type not in {"MESH", "CURVE", "SURFACE", "FONT"}:
        return False
    if obj.name.startswith("V206_"):
        return False
    current = obj.parent
    while current is not None:
        if current == old_rig:
            return True
        current = current.parent
    for modifier in obj.modifiers:
        if modifier.type == "ARMATURE" and modifier.object == old_rig:
            return True
    upper = obj.name.upper()
    return any(token in upper for token in ("FRETTING_HAND", "PICKING_HAND", "HEAD_ASSET", "HAIR", "BEARD", "MUSTACHE"))


def copy_world_control(old_rig, new_rig, name):
    old_bone = old_rig.pose.bones.get(name)
    new_bone = new_rig.pose.bones.get(name)
    if old_bone is None or new_bone is None:
        return False
    new_bone.matrix = new_rig.matrix_world.inverted() @ (old_rig.matrix_world @ old_bone.matrix)
    return True


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    for folder in (STAGE, RENDERS, AUDIT):
        folder.mkdir(parents=True, exist_ok=True)

    old_rig = bpy.data.objects["V239_CLEAN_CHARACTER_RIG"]
    body, rig, collection = append_reom()
    target_height = (old_rig.matrix_world @ old_rig.pose.bones["DEF-spine.006"].tail).z
    source_height = (rig.matrix_world @ rig.pose.bones["DEF-spine.006"].tail).z
    scale = target_height / source_height
    rig.scale = (scale, scale, scale)
    bpy.context.view_layer.update()

    copied_controls = []
    for side in ("L", "R"):
        old_parent = old_rig.pose.bones.get(f"upper_arm_parent.{side}")
        new_parent = rig.pose.bones.get(f"upper_arm_parent.{side}")
        if old_parent and new_parent:
            for prop in ("IK_FK", "IK_Stretch", "pole_vector"):
                if prop in old_parent and prop in new_parent:
                    new_parent[prop] = old_parent[prop]
        for name in (f"hand_ik.{side}", f"upper_arm_ik_target.{side}"):
            if copy_world_control(old_rig, rig, name):
                copied_controls.append(name)
    bpy.context.view_layer.update()

    skin = bpy.data.materials.new("V310_REOM_ALIGNMENT_SKIN")
    skin.use_nodes = True
    bsdf = skin.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (0.30, 0.105, 0.055, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.52
    bsdf.inputs["Subsurface Weight"].default_value = 0.08
    body.data.materials.clear()
    body.data.materials.append(skin)
    for polygon in body.data.polygons:
        polygon.material_index = 0

    old_character = [obj for obj in bpy.data.objects if is_old_character_object(obj, old_rig)]
    old_visibility = {obj.name: obj.hide_render for obj in old_character}
    for obj in old_character:
        obj.hide_render = True

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.look = "AgX - Medium High Contrast"
    camera = bpy.data.objects.get("V287_GUITAR_CAMERA")
    if camera is None:
        camera_data = bpy.data.cameras.new("V310_ALIGNMENT_CAMERA")
        camera = bpy.data.objects.new("V310_ALIGNMENT_CAMERA", camera_data)
        bpy.context.scene.collection.objects.link(camera)

    renders = {
        "reom_full": render(
            scene, camera, RENDERS / "v310_reom_full.png",
            Vector((0.0, -3.75, 1.02)), Vector((0.0, -0.02, 1.0)), 66.0, (900, 1000),
        ),
        "reom_upper": render(
            scene, camera, RENDERS / "v310_reom_upper.png",
            Vector((0.0, -2.25, 1.43)), Vector((0.0, -0.18, 1.39)), 82.0, (1000, 900),
        ),
        "reom_three_quarter": render(
            scene, camera, RENDERS / "v310_reom_three_quarter.png",
            Vector((-1.85, -2.35, 1.48)), Vector((0.0, -0.14, 1.30)), 76.0, (1000, 1000),
        ),
        "fretting_alignment": render(
            scene, camera, RENDERS / "v310_fretting_alignment.png",
            Vector((0.88, -1.55, 1.63)), Vector((0.20, -0.39, 1.36)), 96.0, (1100, 900),
        ),
        "picking_alignment": render(
            scene, camera, RENDERS / "v310_picking_alignment.png",
            Vector((-0.78, -1.50, 1.48)), Vector((-0.12, -0.39, 1.28)), 96.0, (1100, 900),
        ),
    }

    for obj in old_character:
        obj.hide_render = old_visibility[obj.name]
    skin.diffuse_color = (0.06, 0.34, 0.80, 0.72)
    bsdf.inputs["Base Color"].default_value = (0.025, 0.20, 0.66, 1.0)
    renders["opaque_overlay"] = render(
        scene, camera, RENDERS / "v310_opaque_overlay.png",
        Vector((0.0, -3.75, 1.02)), Vector((0.0, -0.02, 1.0)), 66.0, (900, 1000),
    )
    for obj in old_character:
        obj.hide_render = True
    skin.diffuse_color = (0.30, 0.105, 0.055, 1.0)
    bsdf.inputs["Base Color"].default_value = (0.30, 0.105, 0.055, 1.0)

    bpy.context.view_layer.update()
    metrics = {
        "uniform_scale": scale,
        "target_head_height_m": target_height,
        "source_head_height_m": source_height,
        "copied_controls": copied_controls,
        "old_character_hidden_count": len(old_character),
        "hands_world_m": {
            side: {
                "reom": list(rig.matrix_world @ rig.pose.bones[f"DEF-hand.{side}"].head),
                "target": list(old_rig.matrix_world @ old_rig.pose.bones[f"DEF-hand.{side}"].head),
            }
            for side in ("L", "R")
        },
        "shoulders_world_m": {
            side: list(rig.matrix_world @ rig.pose.bones[f"DEF-upper_arm.{side}"].head)
            for side in ("L", "R")
        },
    }
    scene["V310_STATUS"] = "REOM_SCENE_ALIGNMENT_VISUAL_REVIEW_REQUIRED"
    scene["V310_REOM_SCALE"] = scale
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v310-reom-scene-alignment-v1",
        "status": "VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)},
        "reom_source": {"path": str(REOM_SOURCE.relative_to(ROOT)), "sha256": sha(REOM_SOURCE)},
        "collection": collection.name,
        "metrics": metrics,
        "renders": renders,
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha(OUTPUT)},
    }
    (AUDIT / "v310_reom_scene_alignment.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V310_REOM_SCENE_ALIGNMENT_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
