"""Calibrate V298 figured finish and refit controls to the traced body."""

from pathlib import Path
import hashlib
import json

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v298_reference_guitar_body" / "Character_An_reference_guitar_body_v298.blend"
STAGE = ROOT / "production_v299_guitar_body_polish"
OUTPUT = STAGE / "Character_An_guitar_body_polish_v299.blend"
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
    surface = next(node for node in nodes if node.bl_idname == "ShaderNodeBsdfPrincipled")
    bump = next(node for node in nodes if node.bl_idname == "ShaderNodeBump")
    wave.inputs["Scale"].default_value = 8.5
    wave.inputs["Distortion"].default_value = 3.2
    wave.inputs["Detail"].default_value = 3.0
    noise.inputs["Scale"].default_value = 5.0
    noise.inputs["Detail"].default_value = 5.0
    mix.inputs[0].default_value = .23
    ramp.color_ramp.elements[0].position = .10
    ramp.color_ramp.elements[0].color = (.0025, .0035, .0042, 1.0)
    ramp.color_ramp.elements[1].position = .90
    ramp.color_ramp.elements[1].color = (.042, .054, .058, 1.0)
    surface.inputs["Roughness"].default_value = .31
    surface.inputs["Coat Weight"].default_value = .18
    surface.inputs["Coat Roughness"].default_value = .25
    bump.inputs["Strength"].default_value = .055

    placements = {
        "V206_CONTROL_KNOB_1": (.790, -.080, .020),
        "V206_CONTROL_KNOB_2": (.790, -.148, .020),
        "V206_CONTROL_SWITCH_BASE": (.700, -.102, .015),
        "V206_OUTPUT_JACK": (.825, -.166, -.020),
        "V206_STRAP_BUTTON_1": (.405, .155, -.030),
        "V206_STRAP_BUTTON_2": (.935, .070, -.030),
    }
    moved = {}
    for name, location in placements.items():
        obj = bpy.data.objects[name]
        moved[name] = {"from": [float(v) for v in obj.location], "to": list(location)}
        obj.location = location
    toggle = bpy.data.objects["V206_CONTROL_SWITCH_TOGGLE"]
    moved[toggle.name] = {"from": [float(v) for v in toggle.location], "to": [-.085, -.207, 0.0]}
    toggle.location = (-.085, -.207, 0.0)
    bpy.context.view_layer.update()

    scene = bpy.context.scene
    camera = bpy.data.objects["V287_GUITAR_CAMERA"]
    root = bpy.data.objects["V206_GUITAR_ROOT"]
    guitar_center = root.matrix_world @ Vector((.70, 0.0, -.01))
    renders = {
        "full": render(scene, camera, RENDERS / "v299_full.png", Vector((0.0, -3.75, 1.02)), Vector((0.0, -.02, 1.0)), 66.0, (900, 1000)),
        "guitar_front": render(scene, camera, RENDERS / "v299_guitar_front.png", root.matrix_world @ Vector((.70, 0.0, 1.42)), guitar_center, 82.0, (1100, 900)),
        "guitar_beauty": render(scene, camera, RENDERS / "v299_guitar_beauty.png", root.matrix_world @ Vector((.72, -.62, 1.18)), guitar_center, 86.0, (1100, 900)),
    }
    scene["V299_STATUS"] = "GUITAR_BODY_POLISH_VISUAL_REVIEW_REQUIRED"
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v299-guitar-body-polish-v1",
        "status": "VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)},
        "hardware_placements": moved,
        "renders": renders,
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha(OUTPUT)},
    }
    (AUDIT / "v299_guitar_body_polish.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V299_GUITAR_BODY_POLISH_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
