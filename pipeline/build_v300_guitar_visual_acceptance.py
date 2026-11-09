"""Finalize the reference-body presentation without floating edge hardware."""

from pathlib import Path
import hashlib
import json

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v299_guitar_body_polish" / "Character_An_guitar_body_polish_v299.blend"
STAGE = ROOT / "production_v300_guitar_visual_acceptance"
OUTPUT = STAGE / "Character_An_guitar_visual_acceptance_v300.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            digest.update(block)
    return digest.hexdigest()


def point_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(scene, camera, path, location, target, lens, resolution):
    camera.location = location
    camera.data.lens = lens
    point_at(camera, target)
    scene.camera = camera
    scene.render.resolution_x, scene.render.resolution_y = resolution
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(path)}


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    for folder in (STAGE, RENDERS, AUDIT):
        folder.mkdir(parents=True, exist_ok=True)
    material = bpy.data.materials["MAT_V298_SMOKY_QUILT_MAPLE"]
    nodes = material.node_tree.nodes
    wave = next(node for node in nodes if node.bl_idname == "ShaderNodeTexWave")
    noise = next(node for node in nodes if node.bl_idname == "ShaderNodeTexNoise")
    mix = next(node for node in nodes if node.bl_idname == "ShaderNodeMixRGB")
    ramp = next(node for node in nodes if node.bl_idname == "ShaderNodeValToRGB")
    bump = next(node for node in nodes if node.bl_idname == "ShaderNodeBump")
    wave.inputs["Scale"].default_value = 5.0
    wave.inputs["Distortion"].default_value = 5.5
    wave.inputs["Detail"].default_value = 2.5
    noise.inputs["Scale"].default_value = 3.2
    noise.inputs["Detail"].default_value = 4.0
    mix.inputs[0].default_value = .14
    ramp.color_ramp.elements[0].position = .05
    ramp.color_ramp.elements[0].color = (.0045, .0060, .0070, 1.0)
    ramp.color_ramp.elements[1].position = .95
    ramp.color_ramp.elements[1].color = (.014, .020, .022, 1.0)
    bump.inputs["Strength"].default_value = .025

    hidden_edge_hardware = []
    for name in ("V206_OUTPUT_JACK", "V206_STRAP_BUTTON_1", "V206_STRAP_BUTTON_2"):
        obj = bpy.data.objects[name]
        obj.hide_render = True
        hidden_edge_hardware.append(name)
    bpy.context.view_layer.update()

    scene = bpy.context.scene
    camera = bpy.data.objects["V287_GUITAR_CAMERA"]
    root = bpy.data.objects["V206_GUITAR_ROOT"]
    center = root.matrix_world @ Vector((.70, 0.0, -.01))
    renders = {
        "full": render(scene, camera, RENDERS / "v300_full.png", Vector((0.0, -3.75, 1.02)), Vector((0.0, -.02, 1.0)), 66.0, (900, 1000)),
        "guitar_front": render(scene, camera, RENDERS / "v300_guitar_front.png", root.matrix_world @ Vector((.70, 0.0, 1.42)), center, 82.0, (1100, 900)),
        "guitar_beauty": render(scene, camera, RENDERS / "v300_guitar_beauty.png", root.matrix_world @ Vector((.72, -.62, 1.18)), center, 86.0, (1100, 900)),
    }
    scene["V300_STATUS"] = "REFERENCE_BODY_INTERIM_ACCEPTED"
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v300-guitar-visual-acceptance-v1",
        "status": "REFERENCE_BODY_INTERIM_ACCEPTED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)},
        "hidden_pending_edge_orientation": hidden_edge_hardware,
        "renders": renders,
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha(OUTPUT)},
    }
    (AUDIT / "v300_guitar_visual_acceptance.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V300_GUITAR_VISUAL_ACCEPTANCE_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
