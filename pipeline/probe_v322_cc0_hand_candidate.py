"""Render and inventory the CC0 MakeHuman/MPFB hand before scene integration."""

from pathlib import Path
import hashlib
import json

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v321_collision_free_fretting" / "Character_An_collision_free_fretting_v321.blend"
ASSET = ROOT / "third_party" / "cc0_hands" / "innerscene" / "hand-posable-right.glb"
LIBRARY = ROOT / "third_party" / "cc0_hands" / "innerscene" / "hand-posable-right.blend"
STAGE = ROOT / "production_v322_character_rebuild"
RENDERS = STAGE / "renders" / "hand_candidate"
AUDIT = STAGE / "audit" / "v322_cc0_hand_candidate.json"


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            digest.update(block)
    return digest.hexdigest()


def aim(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def world_bounds(objects):
    points = []
    for obj in objects:
        if obj.type != "MESH":
            continue
        points.extend(obj.matrix_world @ Vector(corner) for corner in obj.bound_box)
    lower = Vector(tuple(min(point[axis] for point in points) for axis in range(3)))
    upper = Vector(tuple(max(point[axis] for point in points) for axis in range(3)))
    return lower, upper


def render(scene, camera, path, location, target, lens=92.0):
    camera.location = location
    camera.data.lens = lens
    aim(camera, target)
    scene.camera = camera
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True, scene=scene.name)
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(path)}


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    RENDERS.mkdir(parents=True, exist_ok=True)
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    existing = set(bpy.data.objects)
    with bpy.data.libraries.load(str(LIBRARY), link=False) as (source, target):
        target.objects = list(source.objects)
    imported = [obj for obj in target.objects if obj is not None]
    scene = bpy.data.scenes.new("V322_CC0_HAND_PROBE_SCENE")
    for obj in imported:
        if obj.name not in scene.collection.objects:
            scene.collection.objects.link(obj)
    all_meshes = [obj for obj in imported if obj.type == "MESH"]
    meshes = [
        obj for obj in all_meshes
        if any(modifier.type == "ARMATURE" for modifier in obj.modifiers)
    ]
    armatures = [obj for obj in imported if obj.type == "ARMATURE"]
    if not meshes or not armatures:
        raise RuntimeError("Expected one or more imported meshes and an armature")
    for obj in imported:
        obj.hide_render = obj.type == "MESH" and obj not in meshes
        obj.hide_viewport = False
        obj["V322_CC0_HAND_CANDIDATE"] = True
    preview = bpy.data.materials.new("V322_HAND_PREVIEW")
    preview.use_nodes = True
    bsdf = preview.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (0.22, 0.055, 0.022, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.46
    if "Subsurface Weight" in bsdf.inputs:
        bsdf.inputs["Subsurface Weight"].default_value = 0.07
    for obj in meshes:
        obj.hide_render = False
        obj.visible_camera = True
        obj.data.materials.clear()
        obj.data.materials.append(preview)

    lower, upper = world_bounds(meshes)
    center = (lower + upper) * 0.5
    size = upper - lower
    largest = max(size)

    scene.render.engine = "BLENDER_EEVEE"
    scene.render.image_settings.file_format = "PNG"
    scene.render.resolution_x = 900
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.world = bpy.data.worlds.new("V322_HAND_WORLD")
    scene.world.use_nodes = True
    background = scene.world.node_tree.nodes.get("Background")
    if background:
        background.inputs["Color"].default_value = (0.018, 0.022, 0.028, 1.0)
        background.inputs["Strength"].default_value = 0.22

    for name, direction, energy, size_light in (
        ("V322_HAND_KEY", Vector((-1.4, -1.8, 1.5)), 500.0, 1.0),
        ("V322_HAND_FILL", Vector((1.5, -0.8, 0.7)), 230.0, 1.2),
        ("V322_HAND_RIM", Vector((0.6, 1.4, 1.2)), 360.0, 0.8),
    ):
        data = bpy.data.lights.new(name + "_DATA", "AREA")
        data.energy = energy
        data.shape = "DISK"
        data.size = size_light
        light = bpy.data.objects.new(name, data)
        scene.collection.objects.link(light)
        light.location = center + direction * largest
        aim(light, center)

    camera_data = bpy.data.cameras.new("V322_HAND_CAMERA_DATA")
    camera = bpy.data.objects.new("V322_HAND_CAMERA", camera_data)
    scene.collection.objects.link(camera)
    renders = {
        "front": render(scene, camera, RENDERS / "v322_hand_front.png", center + Vector((0.0, -3.0, 0.0)) * largest, center),
        "side": render(scene, camera, RENDERS / "v322_hand_side.png", center + Vector((3.0, 0.0, 0.0)) * largest, center),
        "oblique": render(scene, camera, RENDERS / "v322_hand_oblique.png", center + Vector((2.1, -2.1, 1.2)) * largest, center),
    }
    record = {
        "schema": "v322-cc0-hand-candidate-v1",
        "source": {"path": str(ASSET.relative_to(ROOT)), "sha256": sha(ASSET), "license": "CC0"},
        "meshes": [
            {
                "name": obj.name,
                "vertices": len(obj.data.vertices),
                "polygons": len(obj.data.polygons),
                "materials": [slot.material.name if slot.material else None for slot in obj.material_slots],
                "armature_modifiers": [modifier.object.name if modifier.object else None for modifier in obj.modifiers if modifier.type == "ARMATURE"],
            }
            for obj in meshes
        ],
        "armatures": [{"name": obj.name, "bones": len(obj.data.bones)} for obj in armatures],
        "bounds_m": {"min": list(lower), "max": list(upper), "size": list(size)},
        "renders": renders,
        "decision": "VISUAL_REVIEW_REQUIRED",
    }
    AUDIT.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V322_CC0_HAND_PROBE=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
