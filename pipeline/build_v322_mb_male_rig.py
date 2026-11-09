"""Build the corrected male character foundation with authored skin and Rigify weights."""

from pathlib import Path
import hashlib
import json
import sys

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
CHARMORPH_PARENT = ROOT / "third_party" / "charmorph" / "v0.4.0-3"
STAGE = ROOT / "production_v322_character_rebuild"
OUTPUT = STAGE / "Character_An_mb_male_rig_v322.blend"
RENDERS = STAGE / "renders" / "male_foundation"
AUDIT = STAGE / "audit" / "v322_mb_male_rig.json"
TARGET_HEIGHT_M = 1.80


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            digest.update(block)
    return digest.hexdigest()


def ensure_rigify():
    if hasattr(bpy.ops.pose, "rigify_generate"):
        return "already_available"
    errors = []
    for module in ("rigify", "bl_ext.blender_org.rigify"):
        try:
            result = bpy.ops.preferences.addon_enable(module=module)
            if hasattr(bpy.ops.pose, "rigify_generate"):
                return f"enabled:{module}:{sorted(result)}"
        except Exception as exc:
            errors.append(f"{module}:{exc}")
    raise RuntimeError("Rigify unavailable: " + " | ".join(errors))


def aim(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def bounds(obj):
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    lower = Vector(tuple(min(point[axis] for point in points) for axis in range(3)))
    upper = Vector(tuple(max(point[axis] for point in points) for axis in range(3)))
    return lower, upper


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


def tune_materials(body):
    skin = next((slot.material for slot in body.material_slots if slot.material and slot.material.name.startswith("charmorph_skin_v2")), None)
    if skin and skin.node_tree:
        nodes = skin.node_tree.nodes
        if "skin_color" in nodes:
            nodes["skin_color"].outputs[0].default_value = (0.180, 0.052, 0.028, 1.0)
        if "skin_roughness" in nodes:
            nodes["skin_roughness"].outputs[0].default_value = 0.48
        if "skin_sss_mix" in nodes:
            nodes["skin_sss_mix"].outputs[0].default_value = 0.18
        if "skin_bump" in nodes:
            nodes["skin_bump"].outputs[0].default_value = 0.04
        if "skin_displacement" in nodes:
            nodes["skin_displacement"].outputs[0].default_value = 0.0
    nails = next((slot.material for slot in body.material_slots if slot.material and slot.material.name.startswith("charmorph_nails_v2")), None)
    if nails and nails.node_tree and "nails_natural_color" in nails.node_tree.nodes:
        nails.node_tree.nodes["nails_natural_color"].outputs[0].default_value = (0.31, 0.105, 0.062, 1.0)
    return {"skin": skin.name if skin else None, "nails": nails.name if nails else None}


def main():
    existing = sys.modules.get("CharMorph")
    if existing is not None:
        try:
            existing.unregister()
        except Exception:
            pass
    bpy.ops.wm.read_homefile(use_empty=True, use_factory_startup=True)
    for folder in (STAGE, RENDERS, AUDIT.parent):
        folder.mkdir(parents=True, exist_ok=True)
    rigify_status = ensure_rigify()
    if str(CHARMORPH_PARENT) not in sys.path:
        sys.path.insert(0, str(CHARMORPH_PARENT))
    bpy.ops.preferences.addon_refresh()
    addon_result = sorted(bpy.ops.preferences.addon_enable(module="CharMorph"))
    import CharMorph
    from CharMorph.common import manager

    ui = bpy.context.window_manager.charmorph_ui
    ui.base_model = "mb_male"
    ui.alt_topo = "<Base>"
    ui.material_mode = "NS"
    ui.material_local = True
    ui.tex_downscale = "UL"
    ui.use_sk = False
    ui.import_morphs = False
    ui.import_expressions = False
    ui.import_cursor_z = False
    result_import = sorted(bpy.ops.charmorph.import_char())
    body = bpy.context.view_layer.objects.active
    body.name = "V322_MB_MALE_BODY"

    morpher = manager.morpher
    if not morpher.set_L1("Latin", True):
        raise RuntimeError("CharMorph Latin material/body type is unavailable")
    morpher.update_presets()
    preset = morpher.presets.get("type_lightbody")
    if preset is None:
        raise RuntimeError("CharMorph type_lightbody preset is unavailable")
    morpher.apply_morph_data(preset, False)
    bpy.context.view_layer.update()
    tuned_materials = tune_materials(body)

    lower, upper = bounds(body)
    scale_factor = TARGET_HEIGHT_M / (upper.z - lower.z)
    body.scale = (scale_factor,) * 3
    bpy.context.view_layer.objects.active = body
    body.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    lower, upper = bounds(body)
    body.location.z -= lower.z
    bpy.context.view_layer.update()

    ui.fitting_char = body
    ui.rig = "tweaked"
    ui.rig_manual_sculpt = False
    ui.rig_manual_joints = False
    ui.rig_manual_weights = False
    ui.rigify_finger_ik = True
    ui.rigify_palm_2sides = True
    ui.rigify_palm_fk = True
    ui.rigify_disable_ik_stretch = True
    result_rig = sorted(bpy.ops.charmorph.rig())
    armature = body.find_armature()
    if armature is None:
        raise RuntimeError("CharMorph rig operator returned without an armature")
    armature.name = "V322_MB_MALE_RIG"
    body.name = "V322_MB_MALE_BODY"
    subdivision = body.modifiers.new("V322_RENDER_SUBDIVISION", "SUBSURF")
    subdivision.levels = 1
    subdivision.render_levels = 2

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.world = bpy.data.worlds.new("V322_WORLD")
    scene.world.color = (0.008, 0.010, 0.014)
    for name, location, energy, size in (
        ("KEY", (-2.4, -3.0, 3.8), 920.0, 2.4),
        ("FILL", (2.5, -1.4, 2.5), 440.0, 2.2),
        ("RIM", (0.0, 2.4, 3.2), 720.0, 1.8),
    ):
        data = bpy.data.lights.new(f"V322_{name}_DATA", "AREA")
        data.energy = energy
        data.shape = "DISK"
        data.size = size
        light = bpy.data.objects.new(f"V322_{name}", data)
        scene.collection.objects.link(light)
        light.location = location
        aim(light, Vector((0.0, 0.0, 1.05)))
    camera_data = bpy.data.cameras.new("V322_CAMERA_DATA")
    camera = bpy.data.objects.new("V322_CAMERA", camera_data)
    scene.collection.objects.link(camera)

    lower, upper = bounds(body)
    center = (lower + upper) * 0.5
    renders = {
        "front": render(scene, camera, RENDERS / "v322_male_front.png", Vector((0.0, -3.45, 1.00)), Vector((0.0, 0.0, 1.00)), 72.0, (900, 1100)),
        "three_quarter": render(scene, camera, RENDERS / "v322_male_three_quarter.png", Vector((2.35, -2.75, 1.13)), Vector((0.0, 0.0, 1.00)), 76.0, (900, 1100)),
    }
    left_points = [body.matrix_world @ vertex.co for vertex in body.data.vertices]
    min_x = min(point.x for point in left_points)
    hand_points = [point for point in left_points if point.x < min_x + 0.23]
    hand_center = sum(hand_points, Vector()) / len(hand_points)
    renders["hand_front"] = render(scene, camera, RENDERS / "v322_male_hand_front.png", hand_center + Vector((0.0, -0.58, 0.02)), hand_center, 96.0, (900, 900))
    renders["hand_oblique"] = render(scene, camera, RENDERS / "v322_male_hand_oblique.png", hand_center + Vector((-0.28, -0.50, 0.18)), hand_center, 96.0, (900, 900))

    scene["V322_STATUS"] = "CORRECTED_MALE_FOUNDATION_VISUAL_REVIEW_REQUIRED"
    scene["V322_REFERENCE_BUILD"] = "CHARMORPH_MB_MALE_LATIN_LIGHTBODY"
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    lower, upper = bounds(body)
    finger_controls = sorted(
        bone.name for bone in armature.pose.bones
        if any(token in bone.name.lower() for token in ("f_index", "f_middle", "f_ring", "f_pinky", "thumb", "palm"))
    )
    record = {
        "schema": "v322-mb-male-rig-v1",
        "status": "CORRECTED_MALE_FOUNDATION_VISUAL_REVIEW_REQUIRED",
        "operators": {"addon_enable": addon_result, "import": result_import, "rig": result_rig},
        "character": {"base": "mb_male", "type": "Latin", "preset": "type_lightbody", "license": "AGPL3"},
        "tuned_materials": tuned_materials,
        "body": {
            "name": body.name,
            "vertices": len(body.data.vertices),
            "polygons": len(body.data.polygons),
            "height_m": upper.z - lower.z,
            "width_m": upper.x - lower.x,
            "materials": [slot.material.name if slot.material else None for slot in body.material_slots],
            "vertex_groups": len(body.vertex_groups),
        },
        "rig": {"name": armature.name, "bones": len(armature.data.bones), "finger_controls": finger_controls},
        "rigify": rigify_status,
        "renders": renders,
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha(OUTPUT)},
    }
    AUDIT.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V322_MB_MALE_RIG_OK=" + json.dumps({
        "height_m": record["body"]["height_m"],
        "vertices": record["body"]["vertices"],
        "bones": record["rig"]["bones"],
        "output_sha256": record["output"]["sha256"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
