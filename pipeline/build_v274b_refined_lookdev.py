"""Correct the V274A material, eye, subdivision, lighting, and groom density failures."""

from pathlib import Path
import hashlib
import json

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v274a_identity_lookdev" / "Character_An_identity_lookdev_v274a.blend"
STAGE = ROOT / "production_v274b_refined_lookdev"
OUTPUT = STAGE / "Character_An_refined_lookdev_v274b.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"
HEAD = "V276E_GEO-head_animation_realistic"


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            digest.update(block)
    return digest.hexdigest()


def point_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def lengthen_curves(obj, factor):
    for spline in obj.data.splines:
        if not spline.points:
            continue
        root = Vector(spline.points[0].co[:3])
        for point in spline.points[1:]:
            current = Vector(point.co[:3])
            updated = root + (current - root) * factor
            point.co = (*updated, 1.0)


def main():
    if Path(bpy.data.filepath).resolve() != SOURCE.resolve():
        raise RuntimeError(f"Open V274A first: {SOURCE}")
    for folder in (STAGE, RENDERS, AUDIT):
        folder.mkdir(parents=True, exist_ok=True)

    head = bpy.data.objects[HEAD]
    for polygon in head.data.polygons:
        polygon.use_smooth = True
    subdivision = head.modifiers.get("V274B_PORTRAIT_SUBDIV") or head.modifiers.new("V274B_PORTRAIT_SUBDIV", "SUBSURF")
    subdivision.subdivision_type = "CATMULL_CLARK"
    subdivision.levels = 2
    subdivision.render_levels = 2

    skin = bpy.data.materials["V274A_SKIN_PHYSICAL"]
    nodes = skin.node_tree.nodes
    ramp = nodes["V274A_SKIN_TONE_RAMP"].color_ramp
    ramp.elements[0].color = (0.018, 0.0045, 0.0018, 1.0)
    ramp.elements[1].color = (0.115, 0.030, 0.010, 1.0)
    nodes["V274A_SKIN_MACRO"].inputs["Scale"].default_value = 7.5
    nodes["V274A_SKIN_PORES"].inputs["Scale"].default_value = 290.0
    bump = next(node for node in nodes if node.bl_idname == "ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.065
    bump.inputs["Distance"].default_value = 0.00009

    for side in ("L", "R"):
        iris = bpy.data.objects[f"V276E_GEO-head_animation_realistic.iris.{side}"]
        iris.scale *= 0.58
        pupil = bpy.data.objects[f"V274A_PUPIL_{side}"]
        pupil.scale *= 0.72
    sclera = bpy.data.materials["V274A_SCLERA"].node_tree.nodes.get("Principled BSDF")
    sclera.inputs["Base Color"].default_value = (0.82, 0.72, 0.62, 1.0)
    iris_shader = bpy.data.materials["V274A_IRIS_BROWN"].node_tree.nodes.get("Principled BSDF")
    iris_shader.inputs["Base Color"].default_value = (0.12, 0.025, 0.004, 1.0)

    groom_adjustments = {
        "V274A_HAIR_UNDERCOAT": (2.15, 0.000115),
        "V274A_HAIR_CURLS": (2.35, 0.000145),
        "V274A_HAIR_HIGHLIGHTS": (2.45, 0.000080),
        "V274A_BROWS": (1.18, 0.000085),
        "V274A_BEARD_STUBBLE": (1.38, 0.000060),
        "V274A_MUSTACHE": (1.34, 0.000066),
    }
    for name, (factor, bevel) in groom_adjustments.items():
        obj = bpy.data.objects[name]
        lengthen_curves(obj, factor)
        obj.data.bevel_depth = bevel
        obj.data.bevel_resolution = 2

    light_values = {
        "V274A_KEY": (245.0, 1.45),
        "V274A_FILL": (95.0, 1.25),
        "V274A_RIM": (185.0, 1.00),
    }
    for name, (energy, size) in light_values.items():
        light = bpy.data.objects[name]
        light.data.energy = energy
        light.data.size = size

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 960
    scene.render.resolution_y = 960
    scene.render.resolution_percentage = 100
    scene.view_settings.look = "AgX - Medium High Contrast"
    camera = bpy.data.objects["V276E_CAMERA"]
    scene.camera = camera
    target = Vector((0.0, -0.02, 1.650))
    views = {
        "front": (Vector((0.0, -1.60, 1.655)), 80.0),
        "left_three_quarter": (Vector((-0.86, -1.24, 1.680)), 84.0),
        "left_profile": (Vector((-1.58, -0.02, 1.665)), 90.0),
    }
    render_records = {}
    for label, (location, lens) in views.items():
        camera.location = location
        camera.data.lens = lens
        point_at(camera, target)
        path = RENDERS / f"v274b_{label}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        render_records[label] = {"path": str(path.relative_to(ROOT)), "sha256": sha256(path)}

    scene["V274B_STATUS"] = "REFINED_IDENTITY_LOOKDEV_VISUAL_REVIEW_REQUIRED"
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v274b-refined-identity-lookdev-v1",
        "status": "BUILT_VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha256(SOURCE)},
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha256(OUTPUT)},
        "subdivision": {"viewport": subdivision.levels, "render": subdivision.render_levels},
        "groom_adjustments": {name: {"length_factor": values[0], "bevel_m": values[1]} for name, values in groom_adjustments.items()},
        "renders": render_records,
    }
    (AUDIT / "v274b_refined_lookdev.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V274B_REFINED_LOOKDEV_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
