"""Create a dedicated right-hand pick grip and improve forearm clearance."""

from pathlib import Path
import hashlib
import json
import math

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v289_explicit_hand_transform" / "Character_An_explicit_hand_transform_v289.blend"
STAGE = ROOT / "production_v290_picking_grip"
OUTPUT = STAGE / "Character_An_picking_grip_v290.blend"
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


def render(scene, camera, path, resolution):
    scene.camera = camera
    scene.render.resolution_x, scene.render.resolution_y = resolution
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(path)}


def flex_digit(pose, digit, degrees):
    values = []
    for joint, angle in enumerate(degrees, start=1):
        bone = pose[f"{digit}.{joint:02d}.R"]
        bone.rotation_mode = "XYZ"
        bone.rotation_euler.x = math.radians(angle)
        values.append((bone.name, angle))
    return values


def make_pick(center, parent_rig):
    # Standard small plectrum silhouette, held just ahead of the thumb/index pinch.
    vertices = [
        center + Vector((-0.010, -0.003, 0.006)),
        center + Vector((0.010, -0.003, 0.006)),
        center + Vector((0.000, -0.003, -0.014)),
    ]
    mesh = bpy.data.meshes.new("V290_PICK_MESH")
    mesh.from_pydata(vertices, [], [(0, 1, 2)])
    mesh.update()
    obj = bpy.data.objects.new("V290_PLECTRUM", mesh)
    bpy.context.scene.collection.objects.link(obj)
    mat = bpy.data.materials.new("V290_PICK_MATERIAL")
    mat.diffuse_color = (0.025, 0.010, 0.055, 1.0)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (0.025, 0.010, 0.055, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.36
    mesh.materials.append(mat)
    solid = obj.modifiers.new("V290_PICK_THICKNESS", "SOLIDIFY")
    solid.thickness = .0008
    world = obj.matrix_world.copy()
    obj.parent = parent_rig
    obj.parent_type = "BONE"
    obj.parent_bone = "DEF-f_index.03.R"
    obj.matrix_world = world
    return obj


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    for folder in (STAGE, RENDERS, AUDIT):
        folder.mkdir(parents=True, exist_ok=True)
    rig = bpy.data.objects[RIG]
    pose = rig.pose.bones
    pole = pose["upper_arm_ik_target.R"]
    pole_world = rig.matrix_world @ pole.matrix
    pole_world.translation = Vector((-0.50, -0.30, 1.20))
    pole.matrix = rig.matrix_world.inverted() @ pole_world

    controls = []
    controls += flex_digit(pose, "f_index", (34.0, 62.0, 38.0))
    controls += flex_digit(pose, "f_middle", (52.0, 76.0, 50.0))
    controls += flex_digit(pose, "f_ring", (58.0, 82.0, 56.0))
    controls += flex_digit(pose, "f_pinky", (62.0, 86.0, 60.0))
    controls += flex_digit(pose, "thumb", (24.0, 32.0, 18.0))
    bpy.context.view_layer.update()
    index_tip = rig.matrix_world @ pose["DEF-f_index.03.R"].tail
    thumb_tip = rig.matrix_world @ pose["DEF-thumb.03.R"].tail
    pinch = index_tip.lerp(thumb_tip, 0.5) + Vector((0.0, -0.004, -0.003))
    pick = make_pick(pinch, rig)

    scene = bpy.context.scene
    camera = bpy.data.objects["V287_GUITAR_CAMERA"]
    views = {
        "full": (Vector((0.0, -3.75, 1.02)), Vector((0.0, -0.02, 1.0)), 66.0, (900, 1000)),
        "picking_macro": (Vector((-1.25, -1.72, 1.27)), Vector((-0.10, -0.34, 1.22)), 96.0, (1200, 900)),
        "three_quarter": (Vector((-2.55, -2.75, 1.14)), Vector((0.0, -0.03, 1.02)), 70.0, (900, 1000)),
    }
    renders = {}
    for label, (location, target, lens, resolution) in views.items():
        camera.location = location
        camera.data.lens = lens
        point_at(camera, target)
        renders[label] = render(scene, camera, RENDERS / f"v290_{label}.png", resolution)
    scene["V290_STATUS"] = "PICKING_GRIP_VISUAL_REVIEW_REQUIRED"
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v290-picking-grip-v1",
        "status": "VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)},
        "pole_world": [-0.50, -0.30, 1.20],
        "controls_deg": controls,
        "pinch_world": [float(value) for value in pinch],
        "pick": pick.name,
        "renders": renders,
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha(OUTPUT)},
    }
    (AUDIT / "v290_picking_grip.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V290_PICKING_GRIP_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
