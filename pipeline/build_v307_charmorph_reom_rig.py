"""Generate a current Rigify2 Reom base with CharMorph's authored weights."""

from pathlib import Path
import hashlib
import json
import sys

import bpy


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
CHARMORPH_PARENT = ROOT / "third_party" / "charmorph" / "v0.4.0-3"
STAGE = ROOT / "production_v307_charmorph_reom_rig"
OUTPUT = STAGE / "Character_An_reom_rig_v307.blend"
AUDIT = STAGE / "audit"


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


def main():
    existing = sys.modules.get("CharMorph")
    if existing is not None:
        try:
            existing.unregister()
        except Exception:
            pass
    bpy.ops.wm.read_homefile(use_empty=True, use_factory_startup=True)
    for folder in (STAGE, AUDIT):
        folder.mkdir(parents=True, exist_ok=True)
    rigify_status = ensure_rigify()
    sys.path.insert(0, str(CHARMORPH_PARENT))
    bpy.ops.preferences.addon_refresh()
    addon_result = sorted(bpy.ops.preferences.addon_enable(module="CharMorph"))
    import CharMorph

    ui = bpy.context.window_manager.charmorph_ui
    ui.base_model = "reom"
    ui.alt_topo = "<Base>"
    ui.use_sk = False
    ui.import_morphs = False
    ui.import_expressions = False
    ui.import_cursor_z = False
    result_import = sorted(bpy.ops.charmorph.import_char())
    body = bpy.context.view_layer.objects.active
    body.name = "V307_REOM_BODY"
    bpy.ops.object.select_all(action="DESELECT")
    body.select_set(True)
    bpy.context.view_layer.objects.active = body
    ui.fitting_char = body

    ui.rig = "rigify2"
    ui.rig_manual_sculpt = False
    ui.rig_manual_joints = False
    ui.rig_manual_weights = False
    ui.rigify_finger_ik = True
    ui.rigify_palm_2sides = True
    ui.rigify_palm_fk = True
    ui.rigify_disable_ik_stretch = True
    bpy.context.view_layer.objects.active = body
    body.select_set(True)
    result_rig = sorted(bpy.ops.charmorph.rig())
    armature = body.find_armature()
    if armature is None:
        raise RuntimeError("CharMorph rig operator returned without an armature")
    armature.name = "V307_REOM_RIG"
    subdivision = body.modifiers.new("V307_RENDER_SUBDIVISION", "SUBSURF")
    subdivision.levels = 1
    subdivision.render_levels = 2

    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    finger_controls = sorted(
        bone.name for bone in armature.pose.bones
        if any(token in bone.name.lower() for token in ("f_index", "f_middle", "f_ring", "f_pinky", "thumb", "palm"))
    )
    record = {
        "schema": "v307-charmorph-reom-rig-v1",
        "status": "RIG_GENERATED_VISUAL_TEST_REQUIRED",
        "rigify": rigify_status,
        "operators": {"addon_enable": addon_result, "import": result_import, "rig": result_rig},
        "body": {
            "name": body.name,
            "vertices": len(body.data.vertices),
            "polygons": len(body.data.polygons),
            "vertex_groups": len(body.vertex_groups),
            "shape_keys": len(body.data.shape_keys.key_blocks) if body.data.shape_keys else 0,
        },
        "rig": {
            "name": armature.name,
            "bones": len(armature.data.bones),
            "pose_bones": len(armature.pose.bones),
            "finger_controls": finger_controls,
        },
        "source": {
            "addon_tag": "v0.4.0-3",
            "addon_commit": "e2e87480657c87eb17bbfbd83833bee628494a90",
            "data_commit": "a8512ac299c0cb1724c7b5417267c94bef024d64",
            "character": "Reom",
            "license": "CC-BY",
        },
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha(OUTPUT)},
    }
    (AUDIT / "v307_charmorph_reom_rig.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V307_CHARMORPH_REOM_RIG_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
