"""Render isolated eye-assembly diagnostics from the V274B checkpoint."""

from pathlib import Path
import json

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v274b_refined_lookdev" / "Character_An_refined_lookdev_v274b.blend"
OUT = ROOT / "diagnostics" / "v274b_eye_assembly"


def point_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def world_bounds(obj):
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    return {
        "min": [min(point[i] for point in points) for i in range(3)],
        "max": [max(point[i] for point in points) for i in range(3)],
        "center": [sum(point[i] for point in points) / len(points) for i in range(3)],
        "dimensions": [max(point[i] for point in points) - min(point[i] for point in points) for i in range(3)],
    }


def material(name, color, metallic=0.0, roughness=0.45):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = color
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Roughness"].default_value = roughness
    return mat


def main():
    if Path(bpy.data.filepath).resolve() != SOURCE.resolve():
        bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    OUT.mkdir(parents=True, exist_ok=True)

    head = bpy.data.objects["V276E_GEO-head_animation_realistic"]
    eyes = {}
    for side in ("L", "R"):
        eyes[side] = {
            "sclera": bpy.data.objects[f"V276E_GEO-head_animation_realistic.sclera.{side}"],
            "iris": bpy.data.objects[f"V276E_GEO-head_animation_realistic.iris.{side}"],
            "pupil": bpy.data.objects[f"V274A_PUPIL_{side}"],
        }

    report = {
        side: {part: world_bounds(obj) | {"parent": obj.parent.name if obj.parent else None}
               for part, obj in pieces.items()}
        for side, pieces in eyes.items()
    }
    report["head"] = world_bounds(head)
    head_points = [head.matrix_world @ vertex.co for vertex in head.data.vertices]
    report["aperture_samples"] = {}
    for side, center_x in (("L", 0.035), ("R", -0.035)):
        samples = sorted(
            point.y for point in head_points
            if abs(point.x - center_x) < 0.024 and abs(point.z - 1.681) < 0.026
        )
        report["aperture_samples"][side] = {
            "count": len(samples),
            "front_min_y": samples[0],
            "front_decile_y": samples[max(0, len(samples) // 10 - 1)],
            "median_y": samples[len(samples) // 2],
            "back_max_y": samples[-1],
        }

    white = material("DIAG_SCLERA_WHITE", (0.88, 0.88, 0.82, 1.0), roughness=0.32)
    amber = material("DIAG_IRIS_AMBER", (0.32, 0.075, 0.008, 1.0), roughness=0.28)
    black = material("DIAG_PUPIL_BLACK", (0.001, 0.001, 0.001, 1.0), roughness=0.2)
    clay = material("DIAG_HEAD_CLAY", (0.22, 0.11, 0.065, 1.0), roughness=0.6)
    head.data.materials.clear()
    head.data.materials.append(clay)
    for pieces in eyes.values():
        for part, mat in (("sclera", white), ("iris", amber), ("pupil", black)):
            pieces[part].data.materials.clear()
            pieces[part].data.materials.append(mat)

    for obj in bpy.data.objects:
        if obj.type in {"LIGHT", "CAMERA"} or obj == head or any(obj in pieces.values() for pieces in eyes.values()):
            continue
        obj.hide_render = True

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1200
    scene.render.resolution_y = 650
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.world.color = (0.035, 0.035, 0.035)
    camera = bpy.data.objects.get("V276E_CAMERA")
    camera.location = Vector((0.0, -0.77, 1.682))
    camera.data.lens = 108
    point_at(camera, Vector((0.0, -0.105, 1.681)))
    scene.camera = camera

    for light in [obj for obj in bpy.data.objects if obj.type == "LIGHT"]:
        light.hide_render = True
    light_data = bpy.data.lights.new("DIAG_EYE_KEY", "AREA")
    light_data.energy = 480.0
    light_data.shape = "DISK"
    light_data.size = 0.55
    light = bpy.data.objects.new("DIAG_EYE_KEY", light_data)
    scene.collection.objects.link(light)
    light.location = Vector((-0.25, -0.55, 1.95))
    point_at(light, Vector((0.0, -0.1, 1.68)))

    states = {
        "sclera_only": (False, True, True),
        "sclera_iris": (False, False, True),
        "full": (False, False, False),
    }
    for label, (hide_sclera, hide_iris, hide_pupil) in states.items():
        for pieces in eyes.values():
            pieces["sclera"].hide_render = hide_sclera
            pieces["iris"].hide_render = hide_iris
            pieces["pupil"].hide_render = hide_pupil
        scene.render.filepath = str(OUT / f"v274b_eye_{label}.png")
        bpy.ops.render.render(write_still=True)

    (OUT / "eye_bounds.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print("V274B_EYE_DIAGNOSTIC_OK=" + json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
