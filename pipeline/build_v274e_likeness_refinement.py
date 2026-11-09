"""Refine V274D likeness, eye scale, skin response, and curl silhouette."""

from pathlib import Path
import hashlib
import json
import math

import bpy
from mathutils import Vector

ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v274d_reference_lookdev" / "Character_An_reference_lookdev_v274d.blend"
STAGE = ROOT / "production_v274e_likeness_refinement"
OUTPUT = STAGE / "Character_An_likeness_refinement_v274e.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"
HEAD = "V276E_GEO-head_animation_realistic"


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            digest.update(block)
    return digest.hexdigest()


def gaussian(v, center, radius):
    return math.exp(-((v - center) / radius) ** 2)


def point_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def refine(world):
    p = world.copy()
    anterior = gaussian(world.y, -0.112, 0.050)
    if anterior < 0.002:
        return p
    ax = abs(world.x)
    sign = 1.0 if world.x >= 0 else -1.0
    jaw = gaussian(world.z, 1.535, 0.062) * gaussian(ax, 0.065, 0.065) * anterior
    p.x += sign * 0.0065 * jaw
    cheek = gaussian(world.z, 1.622, 0.045) * gaussian(ax, 0.075, 0.040) * anterior
    p.x += sign * 0.0035 * cheek
    p.y -= 0.0020 * cheek
    nose = gaussian(world.z, 1.615, 0.030) * gaussian(ax, 0.025, 0.028) * anterior
    p.x += sign * 0.0033 * nose
    tip = gaussian(world.z, 1.638, 0.024) * gaussian(ax, 0.012, 0.020) * anterior
    p.y -= 0.0028 * tip
    lip = gaussian(world.z, 1.570, 0.021) * gaussian(ax, 0.030, 0.042) * anterior
    p.x += sign * 0.0032 * lip * min(1.0, ax / 0.024 + 0.25)
    p.y -= 0.0022 * lip
    lower = gaussian(world.z, 1.558, 0.011) * gaussian(ax, 0.026, 0.038) * anterior
    p.y -= 0.0018 * lower
    return p


def lengthen_curve(obj, factor):
    for spline in obj.data.splines:
        if not spline.points:
            continue
        root = Vector(spline.points[0].co[:3])
        for point in spline.points[1:]:
            co = Vector(point.co[:3])
            point.co = (*(root + (co - root) * factor), 1.0)


def main():
    if Path(bpy.data.filepath).resolve() != SOURCE.resolve():
        bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    for folder in (STAGE, RENDERS, AUDIT):
        folder.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    head = bpy.data.objects[HEAD]
    keys = head.data.shape_keys.key_blocks
    refined = keys["IDENTITY_REFERENCE_SCULPT_V274C"]
    inverse = head.matrix_world.inverted()
    moved, total, maximum = 0, 0.0, 0.0
    for point in refined.data:
        world = head.matrix_world @ point.co
        destination = refine(world)
        distance = (destination - world).length
        if distance > 1e-7:
            point.co = inverse @ destination
            moved += 1
            total += distance
            maximum = max(maximum, distance)

    skin = bpy.data.materials["V274D_SKIN"]
    shader = next(node for node in skin.node_tree.nodes if node.bl_idname == "ShaderNodeBsdfPrincipled")
    ramp = next(node for node in skin.node_tree.nodes if node.bl_idname == "ShaderNodeValToRGB").color_ramp
    ramp.elements[0].color = (0.014, 0.0032, 0.0012, 1.0)
    ramp.elements[1].color = (0.072, 0.017, 0.0052, 1.0)
    shader.inputs["Roughness"].default_value = 0.57
    shader.inputs["Specular IOR Level"].default_value = 0.18
    shader.inputs["Subsurface Weight"].default_value = 0.038

    for side in ("L", "R"):
        iris = bpy.data.objects[f"V274C_IRIS_{side}"]
        iris.scale.x = 1.22
        iris.scale.z = 1.22
        pupil = bpy.data.objects[f"V274C_PUPIL_{side}"]
        pupil.scale.x = 1.08
        pupil.scale.z = 1.08
    sclera_shader = bpy.data.materials["V274D_SCLERA"].node_tree.nodes.get("Principled BSDF")
    sclera_shader.inputs["Base Color"].default_value = (0.55, 0.46, 0.36, 1.0)
    iris_shader = bpy.data.materials["V274D_IRIS"].node_tree.nodes.get("Principled BSDF")
    iris_shader.inputs["Base Color"].default_value = (0.060, 0.012, 0.0025, 1.0)

    adjustments = {
        "V274D_HAIR_BASE": (1.55, 0.00046),
        "V274D_CURL_MASS": (1.72, 0.00070),
        "V274D_CURL_HIGHLIGHTS": (1.68, 0.00038),
        "V274D_BROWS": (1.10, 0.000092),
        "V274D_BEARD": (1.18, 0.000057),
        "V274D_MUSTACHE": (1.15, 0.000064),
    }
    for name, (factor, bevel) in adjustments.items():
        obj = bpy.data.objects[name]
        lengthen_curve(obj, factor)
        obj.data.bevel_depth = bevel
        obj.data.bevel_resolution = 3

    light_setup = {
        "V274D_KEY": (285.0, (1.0, 0.94, 0.88)),
        "V274D_FILL": (110.0, (0.78, 0.84, 1.0)),
        "V274D_RIM": (190.0, (1.0, 0.86, 0.76)),
    }
    for name, (energy, color) in light_setup.items():
        light = bpy.data.objects[name]
        light.data.energy = energy
        light.data.color = color
    scene.world.color = (0.018, 0.016, 0.014)
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.render.resolution_x = 960
    scene.render.resolution_y = 960
    scene.render.resolution_percentage = 100
    camera = bpy.data.objects["V276E_CAMERA"]
    target = Vector((0.0, -0.055, 1.638))
    views = {
        "front": (Vector((0.0, -1.42, 1.638)), 90.0),
        "left_three_quarter": (Vector((-0.79, -1.12, 1.653)), 92.0),
        "left_profile": (Vector((-1.42, -0.01, 1.638)), 96.0),
    }
    renders = {}
    for label, (location, lens) in views.items():
        camera.location = location
        camera.data.lens = lens
        point_at(camera, target)
        path = RENDERS / f"v274e_{label}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        renders[label] = {"path": str(path.relative_to(ROOT)), "sha256": sha(path)}

    scene["V274E_STATUS"] = "LIKENESS_REFINEMENT_VISUAL_REVIEW_REQUIRED"
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v274e-likeness-refinement-v1",
        "status": "BUILT_VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)},
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha(OUTPUT)},
        "sculpt_delta": {"moved_vertices": moved, "mean_m": total / max(1, moved), "max_m": maximum},
        "groom_adjustments": adjustments,
        "renders": renders,
    }
    (AUDIT / "v274e_likeness_refinement.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V274E_LIKENESS_REFINEMENT_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
