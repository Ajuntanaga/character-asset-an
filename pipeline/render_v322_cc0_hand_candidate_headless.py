"""Headless render probe for the converted CC0 hand library."""

from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
RENDERS = ROOT / "production_v322_character_rebuild" / "renders" / "hand_candidate"


def aim(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def main():
    RENDERS.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    hand = max((obj for obj in bpy.data.objects if obj.type == "MESH"), key=lambda obj: len(obj.data.vertices))
    armature = next(modifier.object for modifier in hand.modifiers if modifier.type == "ARMATURE")
    for obj in bpy.data.objects:
        obj.hide_render = obj not in {hand, armature}
    hand.hide_render = False
    hand.visible_camera = True
    preview = bpy.data.materials.new("V322_HAND_PREVIEW_HEADLESS")
    preview.use_nodes = True
    bsdf = preview.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (0.24, 0.065, 0.025, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.46
    if "Subsurface Weight" in bsdf.inputs:
        bsdf.inputs["Subsurface Weight"].default_value = 0.07
    hand.data.materials.clear()
    hand.data.materials.append(preview)

    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = hand.evaluated_get(depsgraph)
    points = [evaluated.matrix_world @ Vector(corner) for corner in evaluated.bound_box]
    lower = Vector(tuple(min(point[axis] for point in points) for axis in range(3)))
    upper = Vector(tuple(max(point[axis] for point in points) for axis in range(3)))
    center = (lower + upper) * 0.5
    largest = max(upper - lower)

    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 900
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.world = scene.world or bpy.data.worlds.new("V322_HAND_WORLD_HEADLESS")
    scene.world.color = (0.012, 0.015, 0.020)
    for name, direction, energy, size in (
        ("KEY", Vector((-1.3, -1.8, 1.5)), 500.0, 1.0),
        ("FILL", Vector((1.4, -0.7, 0.8)), 230.0, 1.2),
        ("RIM", Vector((0.7, 1.4, 1.2)), 340.0, 0.8),
    ):
        data = bpy.data.lights.new("V322_" + name + "_DATA", "AREA")
        data.energy = energy
        data.size = size
        light = bpy.data.objects.new("V322_" + name, data)
        scene.collection.objects.link(light)
        light.location = center + direction * largest
        aim(light, center)
        light.hide_render = False
    camera_data = bpy.data.cameras.new("V322_HAND_CAMERA_DATA")
    camera = bpy.data.objects.new("V322_HAND_CAMERA", camera_data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    for label, direction in (
        ("front", Vector((0.0, -3.5, 0.0))),
        ("side", Vector((3.5, 0.0, 0.0))),
        ("dorsal", Vector((0.0, 0.0, 3.5))),
        ("palm", Vector((0.0, 0.0, -3.5))),
        ("oblique", Vector((2.5, -2.5, 1.2))),
    ):
        camera.location = center + direction * largest
        camera.data.lens = 78.0
        aim(camera, center)
        scene.render.filepath = str(RENDERS / f"v322_hand_{label}.png")
        bpy.ops.render.render(write_still=True)
    print(f"V322_CC0_HAND_HEADLESS_RENDERED={hand.name}:{len(hand.data.vertices)}")


if __name__ == "__main__":
    main()
