"""Render small signed-axis probes for the Rigify right index and thumb controls."""

from pathlib import Path
import hashlib
import json
import math

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v289_explicit_hand_transform" / "Character_An_explicit_hand_transform_v289.blend"
STAGE = ROOT / "production_v291_picking_axis_probe"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"
RIG = "V239_CLEAN_CHARACTER_RIG"


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            digest.update(block)
    return digest.hexdigest()


def point_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    for folder in (STAGE, RENDERS, AUDIT):
        folder.mkdir(parents=True, exist_ok=True)
    rig = bpy.data.objects[RIG]
    pose = rig.pose.bones
    controls = [
        pose["f_index.01.R"],
        pose["f_index.02.R"],
        pose["thumb.01.R"],
        pose["thumb.02.R"],
    ]
    neutral = {bone.name: bone.matrix_basis.copy() for bone in controls}
    scene = bpy.context.scene
    camera = bpy.data.objects["V287_GUITAR_CAMERA"]
    camera.location = Vector((-1.22, -1.66, 1.28))
    camera.data.lens = 100.0
    point_at(camera, Vector((-0.10, -0.35, 1.23)))
    scene.camera = camera
    scene.render.resolution_x = 520
    scene.render.resolution_y = 520
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    records = []
    for bone in controls:
        for axis_index, axis_name in enumerate("xyz"):
            for sign, sign_name in ((-1.0, "neg"), (1.0, "pos")):
                for reset in controls:
                    reset.matrix_basis = neutral[reset.name].copy()
                    reset.rotation_mode = "XYZ"
                bone.rotation_euler[axis_index] += sign * math.radians(32.0)
                bpy.context.view_layer.update()
                label = f"{bone.name.replace('.', '_')}_{axis_name}_{sign_name}"
                path = RENDERS / f"v291_{label}.png"
                scene.render.filepath = str(path)
                bpy.ops.render.render(write_still=True)
                records.append({"control": bone.name, "axis": axis_name, "sign": sign_name, "degrees": 32.0 * sign, "path": str(path.relative_to(ROOT)), "sha256": sha(path)})
    for reset in controls:
        reset.matrix_basis = neutral[reset.name].copy()
    bpy.context.view_layer.update()
    record = {
        "schema": "v291-picking-axis-probe-v1",
        "status": "DIAGNOSTIC_RENDERED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)},
        "probes": records,
    }
    (AUDIT / "v291_picking_axis_probe.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V291_PICKING_AXIS_PROBE_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
