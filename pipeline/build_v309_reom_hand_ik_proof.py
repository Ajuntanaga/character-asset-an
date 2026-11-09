"""Test the Reom hand through its actual Rigify finger IK targets."""

from pathlib import Path
import hashlib
import json

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v307_charmorph_reom_rig" / "Character_An_reom_rig_v307.blend"
STAGE = ROOT / "production_v309_reom_hand_ik_proof"
OUTPUT = STAGE / "Character_An_reom_hand_ik_v309.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"
IK_NAMES = [f"f_{digit}.01_ik.L" for digit in ("index", "middle", "ring", "pinky")] + ["thumb.01_ik.L"]


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            digest.update(block)
    return digest.hexdigest()


def aim(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(scene, camera, path, location, target):
    camera.location = location
    camera.data.lens = 88
    aim(camera, target)
    scene.camera = camera
    scene.render.resolution_x = 1000
    scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(path)}


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    for folder in (STAGE, RENDERS, AUDIT):
        folder.mkdir(parents=True, exist_ok=True)
    body = bpy.data.objects["V307_REOM_BODY"]
    rig = bpy.data.objects["V307_REOM_RIG"]
    clay = bpy.data.materials.new("V309_HAND_CLAY")
    clay.diffuse_color = (.24, .075, .035, 1)
    clay.use_nodes = True
    bsdf = clay.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (.26, .075, .03, 1)
    bsdf.inputs["Roughness"].default_value = .46
    bsdf.inputs["Subsurface Weight"].default_value = .055
    body.data.materials.clear()
    body.data.materials.append(clay)
    for polygon in body.data.polygons:
        polygon.material_index = 0

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.image_settings.file_format = "PNG"
    if scene.world is None:
        scene.world = bpy.data.worlds.new("V309_WORLD")
    scene.world.color = (.004, .004, .006)
    camera_data = bpy.data.cameras.new("V309_HAND_CAMERA")
    camera = bpy.data.objects.new("V309_HAND_CAMERA", camera_data)
    bpy.context.collection.objects.link(camera)
    target = rig.matrix_world @ Vector((.350, .095, .910))
    for name, location, energy, size in (
        ("KEY", target + Vector((.32, -.28, .35)), 300, .35),
        ("FILL", target + Vector((.15, .34, .08)), 180, .30),
        ("RIM", target + Vector((-.30, -.10, .25)), 260, .30),
    ):
        data = bpy.data.lights.new(f"V309_{name}", "AREA")
        data.energy = energy
        data.shape = "DISK"
        data.size = size
        light = bpy.data.objects.new(f"V309_{name}", data)
        light.location = location
        aim(light, target)
        bpy.context.collection.objects.link(light)

    front = target + Vector((.46, 0, .02))
    oblique = target + Vector((.36, -.30, .15))
    renders = {"neutral_palm": render(scene, camera, RENDERS / "v309_neutral_palm.png", front, target)}
    original = {}
    offsets = {
        "f_index.01_ik.L": Vector((-.052, .000, .038)),
        "f_middle.01_ik.L": Vector((-.058, .000, .042)),
        "f_ring.01_ik.L": Vector((-.055, -.002, .040)),
        "f_pinky.01_ik.L": Vector((-.046, -.004, .034)),
        "thumb.01_ik.L": Vector((.018, .040, .026)),
    }
    for name in IK_NAMES:
        bone = rig.pose.bones[name]
        original[name] = list(bone.matrix.translation)
        bone["FK_IK"] = 1.0
        matrix = bone.matrix.copy()
        matrix.translation += offsets[name]
        bone.matrix = matrix
    bpy.context.view_layer.update()
    renders["ik_curl_palm"] = render(scene, camera, RENDERS / "v309_ik_curl_palm.png", front, target)
    renders["ik_curl_oblique"] = render(scene, camera, RENDERS / "v309_ik_curl_oblique.png", oblique, target)

    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v309-reom-hand-ik-proof-v1",
        "status": "VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)},
        "ik_offsets_armature_space_m": {name: list(value) for name, value in offsets.items()},
        "ik_original_armature_space_m": original,
        "renders": renders,
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha(OUTPUT)},
    }
    (AUDIT / "v309_reom_hand_ik_proof.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V309_REOM_HAND_IK_PROOF_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
