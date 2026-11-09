"""Create a film-portrait refinement from V274E with integrated lids and groom mass."""

from pathlib import Path
import hashlib
import json
import math

import bpy
from mathutils import Vector

ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v274e_likeness_refinement" / "Character_An_likeness_refinement_v274e.blend"
STAGE = ROOT / "production_v274f_film_portrait"
OUTPUT = STAGE / "Character_An_film_portrait_v274f.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"
HEAD = "V276E_GEO-head_animation_realistic"


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            digest.update(block)
    return digest.hexdigest()


def gaussian(value, center, radius):
    return math.exp(-((value - center) / radius) ** 2)


def point_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def refine(world):
    p = world.copy()
    anterior = gaussian(world.y, -0.112, 0.052)
    if anterior < 0.002:
        return p
    ax = abs(world.x)
    sign = 1.0 if world.x >= 0.0 else -1.0
    jaw = gaussian(world.z, 1.535, 0.066) * gaussian(ax, 0.068, 0.066) * anterior
    p.x += sign * 0.0055 * jaw
    p.z += 0.0028 * jaw * gaussian(world.z, 1.505, 0.050)
    cheek = gaussian(world.z, 1.625, 0.050) * gaussian(ax, 0.075, 0.042) * anterior
    p.x += sign * 0.0030 * cheek
    brow = gaussian(world.z, 1.702, 0.024) * gaussian(ax, 0.040, 0.050) * anterior
    p.y -= 0.0025 * brow
    # Close the generic wide aperture into the reference's hooded almond eyes.
    eye = gaussian(ax, 0.043, 0.030) * gaussian(world.z, 1.668, 0.025) * anterior
    if world.z > 1.668:
        p.z -= 0.0040 * eye
    else:
        p.z += 0.0024 * eye
    return p


def make_scalp_cap(head, material):
    evaluated = head.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    matrix = evaluated.matrix_world
    kept_faces = []
    kept_vertices = set()
    for polygon in mesh.polygons:
        points = [matrix @ mesh.vertices[index].co for index in polygon.vertices]
        keep = True
        for point in points:
            front = max(0.0, min(1.0, (-point.y + 0.01) / 0.13))
            temple = max(0.0, min(1.0, (abs(point.x) - 0.055) / 0.045))
            line = 1.654 + 0.058 * front + 0.010 * temple
            if point.z < line:
                keep = False
                break
        if keep:
            kept_faces.append(polygon)
            kept_vertices.update(polygon.vertices)
    index_map = {old: new for new, old in enumerate(sorted(kept_vertices))}
    vertices = [matrix @ mesh.vertices[index].co for index in sorted(kept_vertices)]
    faces = [[index_map[index] for index in polygon.vertices] for polygon in kept_faces]
    evaluated.to_mesh_clear()
    cap_mesh = bpy.data.meshes.new("V274F_SCALP_CAP_MESH")
    cap_mesh.from_pydata(vertices, [], faces)
    cap_mesh.update()
    cap = bpy.data.objects.new("V274F_SCALP_CAP", cap_mesh)
    bpy.context.scene.collection.objects.link(cap)
    cap.data.materials.append(material)
    for polygon in cap_mesh.polygons:
        polygon.use_smooth = True
    solidify = cap.modifiers.new("V274F_SCALP_THICKNESS", "SOLIDIFY")
    solidify.thickness = 0.00055
    solidify.offset = 1.0
    return cap, len(faces)


def main():
    if Path(bpy.data.filepath).resolve() != SOURCE.resolve():
        bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    for folder in (STAGE, RENDERS, AUDIT):
        folder.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    head = bpy.data.objects[HEAD]
    key = head.data.shape_keys.key_blocks["IDENTITY_REFERENCE_SCULPT_V274C"]
    inverse = head.matrix_world.inverted()
    moved, total, maximum = 0, 0.0, 0.0
    for point in key.data:
        world = head.matrix_world @ point.co
        destination = refine(world)
        distance = (destination - world).length
        if distance > 1e-7:
            point.co = inverse @ destination
            moved += 1
            total += distance
            maximum = max(maximum, distance)
    bpy.context.view_layer.update()

    skin = bpy.data.materials["V274D_SKIN"]
    ramp = next(node for node in skin.node_tree.nodes if node.bl_idname == "ShaderNodeValToRGB").color_ramp
    ramp.elements[0].color = (0.012, 0.0045, 0.0023, 1.0)
    ramp.elements[1].color = (0.062, 0.027, 0.013, 1.0)
    shader = next(node for node in skin.node_tree.nodes if node.bl_idname == "ShaderNodeBsdfPrincipled")
    shader.inputs["Roughness"].default_value = 0.60
    shader.inputs["Specular IOR Level"].default_value = 0.16

    hair_material = bpy.data.materials["V274D_HAIR"]
    hair_shader = hair_material.node_tree.nodes.get("V274D_HAIR_FIBER_PRINCIPLED")
    hair_shader.inputs["Base Color"].default_value = (0.0007, 0.00045, 0.00028, 1.0)
    hair_shader.inputs["Roughness"].default_value = 0.55
    hair_shader.inputs["Specular IOR Level"].default_value = 0.18
    hair_shader.inputs["Anisotropic"].default_value = 0.35
    warm = bpy.data.materials["V274D_HAIR_WARM"].node_tree.nodes.get("V274D_HAIR_WARM_FIBER_PRINCIPLED")
    warm.inputs["Base Color"].default_value = (0.0020, 0.0009, 0.00045, 1.0)
    warm.inputs["Roughness"].default_value = 0.58
    warm.inputs["Specular IOR Level"].default_value = 0.16

    for name in ("V274D_HAIR_BASE", "V274D_CURL_MASS", "V274D_CURL_HIGHLIGHTS", "V274D_BROWS", "V274D_BEARD", "V274D_MUSTACHE"):
        obj = bpy.data.objects[name]
        for spline in obj.data.splines:
            count = len(spline.points)
            for index, point in enumerate(spline.points):
                t = index / max(1, count - 1)
                point.radius = max(0.06, math.sin(math.pi * min(0.92, t + 0.08)) ** 0.35 * (1.0 - 0.86 * t))
    bpy.data.objects["V274D_CURL_MASS"].data.bevel_depth = 0.00056
    bpy.data.objects["V274D_HAIR_BASE"].data.bevel_depth = 0.00038
    bpy.data.objects["V274D_CURL_HIGHLIGHTS"].data.bevel_depth = 0.00026
    bpy.data.objects["V274D_BROWS"].data.bevel_depth = 0.000085

    cap_material = bpy.data.materials.get("V274F_SCALP_MAT") or bpy.data.materials.new("V274F_SCALP_MAT")
    cap_material.use_nodes = True
    cap_shader = cap_material.node_tree.nodes.get("Principled BSDF")
    cap_shader.inputs["Base Color"].default_value = (0.0010, 0.00055, 0.00030, 1.0)
    cap_shader.inputs["Roughness"].default_value = 0.66
    cap_shader.inputs["Specular IOR Level"].default_value = 0.12
    cap, cap_faces = make_scalp_cap(head, cap_material)

    for side in ("L", "R"):
        sclera = bpy.data.materials["V274D_SCLERA"].node_tree.nodes.get("Principled BSDF")
        sclera.inputs["Base Color"].default_value = (0.48, 0.40, 0.31, 1.0)
        sclera.inputs["Roughness"].default_value = 0.23
        sclera.inputs["Specular IOR Level"].default_value = 0.42
        iris = bpy.data.materials["V274D_IRIS"].node_tree.nodes.get("Principled BSDF")
        iris.inputs["Coat Weight"].default_value = 0.24
        iris.inputs["Coat Roughness"].default_value = 0.08

    for name, energy in (("V274D_KEY", 250.0), ("V274D_FILL", 120.0), ("V274D_RIM", 145.0)):
        bpy.data.objects[name].data.energy = energy
    scene.world.color = (0.024, 0.021, 0.019)
    scene.render.resolution_x = 1024
    scene.render.resolution_y = 1024
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
        path = RENDERS / f"v274f_{label}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        renders[label] = {"path": str(path.relative_to(ROOT)), "sha256": sha(path)}

    scene["V274F_STATUS"] = "FILM_PORTRAIT_VISUAL_REVIEW_REQUIRED"
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v274f-film-portrait-v1",
        "status": "BUILT_VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)},
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha(OUTPUT)},
        "identity_delta": {"moved_vertices": moved, "mean_m": total / max(1, moved), "max_m": maximum},
        "scalp_cap_faces": cap_faces,
        "renders": renders,
    }
    (AUDIT / "v274f_film_portrait.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V274F_FILM_PORTRAIT_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
