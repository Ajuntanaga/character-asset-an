"""Create a dedicated, surface-fitted fretting-hand armature parented to V239."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v248_topology_hand_replacement" / "Character_An_topology_hand_v248.blend"
STAGE = ROOT / "production_v250_dedicated_hand_rig"
OUTPUT = STAGE / "Character_An_dedicated_hand_rig_v250.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"
MAIN_RIG = "V239_CLEAN_CHARACTER_RIG"
HAND = "V248_FRETTING_HAND_REALISTIC"

WRIST = Vector((0.352, 0.0, 1.055))
PALM = Vector((0.399, -0.008, 0.993))
DIGITS = {
    "index": (Vector((0.4173, -0.0507, 0.9797)), Vector((0.4406, -0.0405, 0.8856))),
    "middle": (Vector((0.4213, -0.0247, 0.9804)), Vector((0.4462, -0.0234, 0.8749))),
    "ring": (Vector((0.4230, 0.0033, 0.9797)), Vector((0.4456, -0.0011, 0.8806))),
    "pinky": (Vector((0.4221, 0.0312, 0.9727)), Vector((0.4380, 0.0254, 0.8977))),
    "thumb": (Vector((0.3680, -0.0118, 1.0128)), Vector((0.4178, -0.0557, 0.9410))),
}
PROPORTIONS = {
    "index": (0.47, 0.31, 0.22),
    "middle": (0.46, 0.32, 0.22),
    "ring": (0.47, 0.32, 0.21),
    "pinky": (0.48, 0.31, 0.21),
    "thumb": (0.42, 0.34, 0.24),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def point_at(obj: bpy.types.Object, target: Vector) -> None:
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def activate(obj: bpy.types.Object) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def main() -> None:
    if Path(bpy.data.filepath).resolve() != SOURCE.resolve():
        raise RuntimeError(f"Open V248 first: {SOURCE}")
    STAGE.mkdir(parents=True, exist_ok=True)
    RENDERS.mkdir(parents=True, exist_ok=True)
    AUDIT.mkdir(parents=True, exist_ok=True)
    main_rig = bpy.data.objects[MAIN_RIG]
    hand = bpy.data.objects[HAND]
    main_rig.data.pose_position = "REST"
    bpy.context.view_layer.update()

    hand_world = hand.matrix_world.copy()
    hand.parent = None
    hand.matrix_world = hand_world
    for modifier in tuple(hand.modifiers):
        if modifier.type == "ARMATURE":
            hand.modifiers.remove(modifier)
    hand.vertex_groups.clear()

    armature_data = bpy.data.armatures.new("V250_FRETTING_HAND_RIG_DATA")
    armature = bpy.data.objects.new("V250_FRETTING_HAND_RIG", armature_data)
    bpy.context.scene.collection.objects.link(armature)
    activate(armature)
    bpy.ops.object.mode_set(mode="EDIT")
    root = armature_data.edit_bones.new("hand_root")
    root.head = WRIST
    root.tail = PALM
    root.use_deform = True
    for digit, (start, tip) in DIGITS.items():
        direction = tip - start
        cumulative = 0.0
        parent = root
        for index, proportion in enumerate(PROPORTIONS[digit], start=1):
            bone = armature_data.edit_bones.new(f"{digit}_{index:02d}")
            bone.head = start + direction * cumulative
            cumulative += proportion
            bone.tail = start + direction * cumulative
            bone.parent = parent
            bone.use_connect = index > 1
            bone.use_deform = True
            parent = bone
    bpy.ops.object.mode_set(mode="OBJECT")

    activate(hand)
    armature.select_set(True)
    bpy.context.view_layer.objects.active = armature
    with bpy.context.temp_override(
        active_object=armature,
        object=armature,
        selected_objects=[hand, armature],
        selected_editable_objects=[hand, armature],
    ):
        bpy.ops.object.parent_set(type="ARMATURE_AUTO")
    modifier = next((item for item in hand.modifiers if item.type == "ARMATURE"), None)
    if modifier is None:
        raise RuntimeError("Dedicated hand automatic weights failed")
    modifier.name = "V250_DEDICATED_HAND_ARMATURE"
    modifier.use_deform_preserve_volume = True

    # ARMATURE_AUTO also object-parents the mesh to the armature. The modifier
    # already evaluates the armature object's transform; retaining that object
    # parent would apply wrist motion twice after this armature is bone-parented
    # to the main character. Clear only the object parent and preserve world.
    hand_world_after_bind = hand.matrix_world.copy()
    hand.parent = None
    hand.matrix_world = hand_world_after_bind

    # Use one shared wrist hub for both mesh and local armature. This makes the
    # character wrist motion a rigid common transform while the Armature
    # modifier sees only relative finger deformation; neither double-motion nor
    # a left-behind surface is possible.
    hub = bpy.data.objects.new("V250_FRETTING_HAND_HUB", None)
    bpy.context.scene.collection.objects.link(hub)
    hub_world = hub.matrix_world.copy()
    hub.parent = main_rig
    hub.parent_type = "BONE"
    hub.parent_bone = "DEF-hand.L"
    hub.matrix_world = hub_world
    armature_world = armature.matrix_world.copy()
    armature.parent = hub
    armature.matrix_world = armature_world
    hand_world_after_hub = hand.matrix_world.copy()
    hand.parent = hub
    hand.matrix_world = hand_world_after_hub

    main_rig.data.pose_position = "POSE"
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.look = "AgX - Medium High Contrast"
    camera = bpy.data.objects["CAM_V211_FRONT"]
    camera.data.type = "PERSP"

    def render(label: str) -> Path:
        camera.location = Vector((0.72, -1.48, 1.49))
        camera.data.lens = 105.0
        point_at(camera, Vector((0.27, -0.39, 1.39)))
        scene.camera = camera
        scene.render.resolution_x = 1200
        scene.render.resolution_y = 900
        scene.render.resolution_percentage = 100
        path = RENDERS / f"v250_{label}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        return path

    neutral = render("neutral")
    controls = []
    for digit in ("index", "middle", "ring", "pinky"):
        for joint, angle in zip((1, 2, 3), (0.18, 0.75, 0.48)):
            control = armature.pose.bones[f"{digit}_{joint:02d}"]
            control.rotation_mode = "XYZ"
            control.rotation_euler.x = angle
            controls.append(control)
    for joint, angle in zip((1, 2, 3), (0.14, 0.48, 0.32)):
        control = armature.pose.bones[f"thumb_{joint:02d}"]
        control.rotation_mode = "XYZ"
        control.rotation_euler.x = angle
        controls.append(control)
    bpy.context.view_layer.update()
    flex = render("flex_test")
    for control in controls:
        control.rotation_euler = (0.0, 0.0, 0.0)
    bpy.context.view_layer.update()

    scene["V250_STATUS"] = "DEDICATED_SURFACE_FITTED_HAND_RIG_VISUAL_REVIEW_REQUIRED"
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v250-dedicated-hand-rig-v1",
        "status": "BUILT_VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha256(SOURCE)},
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha256(OUTPUT)},
        "main_rig": MAIN_RIG,
        "hand_rig": armature.name,
        "wrist_hub": hub.name,
        "parent_bone": hub.parent_bone,
        "deform_bones": sum(1 for bone in armature.data.bones if bone.use_deform),
        "hand_vertex_groups": len(hand.vertex_groups),
        "renders": {
            "neutral": {"path": str(neutral.relative_to(ROOT)), "sha256": sha256(neutral)},
            "flex_test": {"path": str(flex.relative_to(ROOT)), "sha256": sha256(flex)},
        },
    }
    (AUDIT / "v250_dedicated_hand_rig.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("V250_DEDICATED_HAND_RIG_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
