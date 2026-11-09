"""Reactivate the fitted FaceBuilder identity stack on the clean Reom rig."""

from pathlib import Path
import hashlib
import json
import math

import bpy
from mathutils import Matrix, Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v310_reom_scene_alignment" / "Character_An_reom_scene_alignment_v310.blend"
STAGE = ROOT / "production_v316_identity_reactivation"
OUTPUT = STAGE / "Character_An_identity_reactivation_v316.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"
BODY = "V310_REOM_BODY"
RIG = "V310_REOM_RIG"
HEAD = "V216_REFERENCE_FITTED_HEAD"
IDENTITY_OBJECTS = (
    HEAD,
    "V216_EYE_L", "V216_EYE_R",
    "V216_IRIS_L", "V216_IRIS_R",
    "V216_PUPIL_L", "V216_PUPIL_R",
    "V217_TIGHT_CURL_GROOM",
)
HEAD_GROUP_PREFIXES = (
    "def-forehead", "def-jaw", "def-brow", "def-cheek", "def-ear",
    "def-eye", "def-lid", "def-lip", "def-nose", "def-temple",
)


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


def remove_charmorph_handlers():
    removed = []
    for handler in list(bpy.app.handlers.depsgraph_update_post):
        if getattr(handler, "__module__", "").startswith("CharMorph"):
            bpy.app.handlers.depsgraph_update_post.remove(handler)
            removed.append(f"{handler.__module__}.{handler.__name__}")
    return removed


def parent_to_head_bone(obj, rig):
    world = obj.matrix_world.copy()
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = "head"
    obj.matrix_world = world


def install_head_mask(body):
    group = body.vertex_groups.get("V316_HIDE_REOM_HEAD") or body.vertex_groups.new(name="V316_HIDE_REOM_HEAD")
    source_group_names = {
        vertex_group.index: vertex_group.name
        for vertex_group in body.vertex_groups
        if vertex_group.name != group.name
    }
    hidden = []
    for vertex in body.data.vertices:
        names = [source_group_names.get(weight.group, "").lower() for weight in vertex.groups if weight.weight > 0.035]
        hide = "def-spine.006" in names or any(name.startswith(HEAD_GROUP_PREFIXES) for name in names)
        if hide:
            hidden.append(vertex.index)
    if not hidden:
        raise RuntimeError("Reom head-mask selection is empty")
    group.add(hidden, 1.0, "REPLACE")
    modifier = body.modifiers.get("V316_HIDE_GENERIC_HEAD") or body.modifiers.new("V316_HIDE_GENERIC_HEAD", "MASK")
    modifier.vertex_group = group.name
    modifier.invert_vertex_group = True
    body.modifiers.move(body.modifiers.find(modifier.name), 0)
    return {"vertex_group": group.name, "hidden_vertices": len(hidden), "modifier": modifier.name}


def portrait_lights(scene, target):
    created = []
    for name, location, energy, size, color in (
        ("V316_KEY", (-0.70, -1.10, 2.05), 255.0, 0.85, (1.0, 0.90, 0.82)),
        ("V316_FILL", (0.82, -0.72, 1.78), 90.0, 0.78, (0.70, 0.82, 1.0)),
        ("V316_RIM", (0.40, 0.44, 2.02), 145.0, 0.65, (1.0, 0.72, 0.54)),
    ):
        data = bpy.data.lights.new(name + "_DATA", "AREA")
        data.energy = energy
        data.shape = "DISK"
        data.size = size
        data.color = color
        light = bpy.data.objects.new(name, data)
        scene.collection.objects.link(light)
        light.location = location
        aim(light, target)
        created.append(light.name)
    return created


def clear_facs(head):
    keys = head.data.shape_keys.key_blocks
    for key in keys[1:]:
        key.value = 0.0
    bpy.context.view_layer.update()
    return keys


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    removed_handlers = remove_charmorph_handlers()
    for folder in (STAGE, RENDERS, AUDIT):
        folder.mkdir(parents=True, exist_ok=True)
    body = bpy.data.objects[BODY]
    rig = bpy.data.objects[RIG]
    missing = [name for name in IDENTITY_OBJECTS if name not in bpy.data.objects]
    if missing:
        raise RuntimeError(f"V310 identity stack incomplete: {missing}")

    head = bpy.data.objects[HEAD]
    shape_count = len(head.data.shape_keys.key_blocks) - 1 if head.data.shape_keys else 0
    if shape_count != 51:
        raise RuntimeError(f"Expected 51 fitted-head FACS shapes, found {shape_count}")
    identity_parenting = {}
    for name in IDENTITY_OBJECTS:
        obj = bpy.data.objects[name]
        identity_parenting[name] = {
            "old_parent": obj.parent.name if obj.parent else None,
            "old_parent_type": obj.parent_type,
            "old_parent_bone": obj.parent_bone,
        }
        parent_to_head_bone(obj, rig)
        obj.hide_render = False
        obj.hide_viewport = False
    for name in ("V217_CURL_CLUSTERS", "V217_BROWS", "V217_BEARD_STUBBLE"):
        obj = bpy.data.objects.get(name)
        if obj:
            obj.hide_render = True
            obj.hide_viewport = True

    mask = install_head_mask(body)
    keys = clear_facs(head)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.world.use_nodes = True
    background = scene.world.node_tree.nodes.get("Background")
    if background:
        background.inputs["Color"].default_value = (0.004, 0.005, 0.007, 1.0)
        background.inputs["Strength"].default_value = 0.11
    target = Vector((0.0, -0.025, 1.64))
    lights = portrait_lights(scene, target)
    camera_data = bpy.data.cameras.new("V316_PORTRAIT_CAMERA_DATA")
    camera = bpy.data.objects.new("V316_PORTRAIT_CAMERA", camera_data)
    scene.collection.objects.link(camera)

    renders = {
        "portrait_front": render(scene, camera, RENDERS / "v316_portrait_front.png", Vector((0.0, -1.48, 1.66)), target, 96.0, (900, 900)),
        "portrait_three_quarter": render(scene, camera, RENDERS / "v316_portrait_three_quarter.png", Vector((0.66, -1.30, 1.70)), target, 92.0, (900, 900)),
        "portrait_profile": render(scene, camera, RENDERS / "v316_portrait_profile.png", Vector((1.34, -0.05, 1.66)), target, 92.0, (900, 900)),
    }
    keys["mouthSmileLeft"].value = 0.82
    keys["mouthSmileRight"].value = 0.82
    keys["cheekSquintLeft"].value = 0.20
    keys["cheekSquintRight"].value = 0.20
    bpy.context.view_layer.update()
    renders["facs_smile"] = render(scene, camera, RENDERS / "v316_facs_smile.png", Vector((0.0, -1.48, 1.66)), target, 96.0, (900, 900))
    clear_facs(head)

    head_control = rig.pose.bones["head"]
    saved_head_matrix = head_control.matrix.copy()
    world = rig.matrix_world @ head_control.matrix
    pivot = world.translation.copy()
    world = Matrix.Translation(pivot) @ Matrix.Rotation(math.radians(18.0), 4, "Z") @ Matrix.Translation(-pivot) @ world
    head_control.matrix = rig.matrix_world.inverted() @ world
    bpy.context.view_layer.update()
    renders["head_turn"] = render(scene, camera, RENDERS / "v316_head_turn.png", Vector((0.0, -1.48, 1.66)), target, 96.0, (900, 900))
    head_control.matrix = saved_head_matrix
    bpy.context.view_layer.update()
    renders["full_integration"] = render(scene, camera, RENDERS / "v316_full_integration.png", Vector((0.0, -3.75, 1.02)), Vector((0.0, -0.02, 1.0)), 66.0, (900, 1000))

    neutral_error = max(abs(key.value) for key in keys[1:])
    scene["V316_STATUS"] = "REFERENCE_IDENTITY_REACTIVATED_VISUAL_REVIEW_REQUIRED"
    scene["V316_FACS_COUNT"] = shape_count
    scene["V316_HEAD_MASK_VERTICES"] = mask["hidden_vertices"]
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v316-identity-reactivation-v1",
        "status": "BUILT_VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)},
        "body": BODY,
        "rig": RIG,
        "identity_objects": list(IDENTITY_OBJECTS),
        "identity_parenting": identity_parenting,
        "head_mask": mask,
        "facs_count": shape_count,
        "neutral_return_max_control": neutral_error,
        "removed_session_handlers": removed_handlers,
        "lights": lights,
        "renders": renders,
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha(OUTPUT)},
    }
    (AUDIT / "v316_identity_reactivation.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V316_IDENTITY_REACTIVATION_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
