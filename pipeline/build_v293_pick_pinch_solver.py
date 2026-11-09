"""Solve a dedicated picking-hand thumb/index pinch and reseat the plectrum."""

from pathlib import Path
import hashlib
import json

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v292_dedicated_picking_hand" / "Character_An_dedicated_picking_hand_v292.blend"
STAGE = ROOT / "production_v293_pick_pinch_solver"
OUTPUT = STAGE / "Character_An_pick_pinch_v293.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"
RIG = "V292_PICKING_HAND_RIG"
HAND = "V292_PICKING_HAND_REALISTIC"


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            digest.update(block)
    return digest.hexdigest()


def point_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def tips(rig):
    return (
        rig.matrix_world @ rig.pose.bones["index_03"].tail,
        rig.matrix_world @ rig.pose.bones["thumb_03"].tail,
    )


def solve_pinch(rig):
    pose = rig.pose.bones
    index_tip, thumb_tip = tips(rig)
    desired_midpoint = index_tip.lerp(thumb_tip, .5)
    variables = [
        (pose["index_01"], 0, -.45, .80),
        (pose["index_01"], 1, -.55, .55),
        (pose["index_01"], 2, -.55, .55),
        (pose["index_02"], 0, 0.0, 1.35),
        (pose["index_02"], 1, -.35, .35),
        (pose["index_03"], 0, 0.0, 1.10),
        (pose["thumb_01"], 0, -.80, .80),
        (pose["thumb_01"], 1, -.80, .80),
        (pose["thumb_01"], 2, -.80, .80),
        (pose["thumb_02"], 0, -.20, 1.20),
        (pose["thumb_02"], 1, -.65, .65),
        (pose["thumb_02"], 2, -.65, .65),
        (pose["thumb_03"], 0, -.20, .90),
    ]
    for bone, _axis, _lower, _upper in variables:
        bone.rotation_mode = "XYZ"

    def objective():
        index, thumb = tips(rig)
        midpoint = index.lerp(thumb, .5)
        separation = (index - thumb).length_squared
        center_drift = (midpoint - desired_midpoint).length_squared
        regularizer = 0.0000015 * sum(float(bone.rotation_euler[axis]) ** 2 for bone, axis, _lower, _upper in variables)
        return separation + center_drift * .45 + regularizer

    best = objective()
    evaluations = 1
    for step in (.34, .18, .095, .048, .024, .012):
        for _ in range(5):
            improved = False
            for bone, axis, lower, upper in variables:
                base = float(bone.rotation_euler[axis])
                local_best = best
                local_value = base
                for candidate in (max(lower, base - step), min(upper, base + step)):
                    bone.rotation_euler[axis] = candidate
                    bpy.context.view_layer.update()
                    value = objective()
                    evaluations += 1
                    if value < local_best:
                        local_best = value
                        local_value = candidate
                bone.rotation_euler[axis] = local_value
                bpy.context.view_layer.update()
                if local_best + 1e-14 < best:
                    best = local_best
                    improved = True
            if not improved:
                break
    index_tip, thumb_tip = tips(rig)
    return {
        "index_tip_world": [float(v) for v in index_tip],
        "thumb_tip_world": [float(v) for v in thumb_tip],
        "pinch_midpoint_world": [float(v) for v in index_tip.lerp(thumb_tip, .5)],
        "tip_separation_m": float((index_tip - thumb_tip).length),
        "evaluations": evaluations,
        "rotations_xyz_rad": {bone.name: [float(v) for v in bone.rotation_euler] for bone, _axis, _lower, _upper in variables},
    }


def create_pick(center):
    old = bpy.data.objects.get("V292_PLECTRUM")
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    vertices = [(-.009, 0.0, .006), (.009, 0.0, .006), (0.0, 0.0, -.013)]
    mesh = bpy.data.meshes.new("V293_PLECTRUM_MESH")
    mesh.from_pydata(vertices, [], [(0, 1, 2)])
    mesh.update()
    obj = bpy.data.objects.new("V293_PLECTRUM", mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = center + Vector((0.0, -.004, 0.0))
    material = bpy.data.materials.get("V292_PLECTRUM_PURPLE") or bpy.data.materials.new("V293_PLECTRUM_PURPLE")
    material.diffuse_color = (.04, .01, .09, 1.0)
    mesh.materials.append(material)
    solid = obj.modifiers.new("V293_PICK_THICKNESS", "SOLIDIFY")
    solid.thickness = .0008
    return obj


def render(scene, camera, path, resolution):
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
    hand = bpy.data.objects[HAND]
    body_material = bpy.data.materials["MAT_V211_NEUTRAL_CLAY"]
    hand.data.materials.clear()
    hand.data.materials.append(body_material)
    rig = bpy.data.objects[RIG]
    result = solve_pinch(rig)
    pick = create_pick(Vector(result["pinch_midpoint_world"]))
    bpy.context.view_layer.update()

    scene = bpy.context.scene
    camera = bpy.data.objects["V287_GUITAR_CAMERA"]
    views = {
        "full": (Vector((0.0, -3.75, 1.02)), Vector((0.0, -0.02, 1.0)), 66.0, (900, 1000)),
        "picking_macro": (Vector((-1.22, -1.66, 1.28)), Vector((-0.10, -0.35, 1.23)), 100.0, (1200, 900)),
        "three_quarter": (Vector((-2.55, -2.75, 1.14)), Vector((0.0, -0.03, 1.02)), 70.0, (900, 1000)),
    }
    renders = {}
    for label, (location, target, lens, resolution) in views.items():
        camera.location = location
        camera.data.lens = lens
        point_at(camera, target)
        renders[label] = render(scene, camera, RENDERS / f"v293_{label}.png", resolution)
    scene["V293_STATUS"] = "PICK_PINCH_VISUAL_REVIEW_REQUIRED"
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v293-pick-pinch-solver-v1",
        "status": "VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)},
        "solve": result,
        "pick": pick.name,
        "material": body_material.name,
        "renders": renders,
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha(OUTPUT)},
    }
    (AUDIT / "v293_pick_pinch_solver.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V293_PICK_PINCH_SOLVER_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
