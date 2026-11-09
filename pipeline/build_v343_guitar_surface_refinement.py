"""Refine the image-derived guitar contour and correct its overlit finish."""
from pathlib import Path
import hashlib
import json

import bpy
from mathutils import Vector

ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v342_graphite_contour_guitar" / "Character_An_graphite_contour_guitar_v342.blend"
CONTOUR = ROOT / "production_v340_image_contour_body" / "analysis" / "strandberg_product_contour.json"
STAGE = ROOT / "production_v343_guitar_surface_refinement"
OUTPUT = STAGE / "Character_An_guitar_surface_refinement_v343.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit" / "v343_guitar_surface_refinement.json"


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1048576), b""):
            digest.update(block)
    return digest.hexdigest()


def chaikin(points, passes=2):
    result = list(points)
    for _ in range(passes):
        refined = []
        for index, point in enumerate(result):
            nxt = result[(index + 1) % len(result)]
            refined.extend((
                (point[0] * .75 + nxt[0] * .25, point[1] * .75 + nxt[1] * .25),
                (point[0] * .25 + nxt[0] * .75, point[1] * .25 + nxt[1] * .75),
            ))
        result = refined
    return result


def contour_points():
    data = json.loads(CONTOUR.read_text())
    width, height = data["image_size"]
    raw = [(u, v) for u, v in data["points_px"] if not (width * .34 < u < width * .59 and v < height * .36)]
    min_u, max_u = min(u for u, _ in raw), max(u for u, _ in raw)
    min_v, max_v = min(v for _, v in raw), max(v for _, v in raw)
    mapped = [
        (.345 + (v - min_v) / (max_v - min_v) * .505,
         (max_u + min_u - 2 * u) / (max_u - min_u) * .165)
        for u, v in raw
    ]
    return mapped, chaikin(mapped, 2)


def prism_mesh(name, points, z0=-.039, z1=.003):
    count = len(points)
    vertices = [(x, y, z0) for x, y in points] + [(x, y, z1) for x, y in points]
    faces = [tuple(range(count - 1, -1, -1)), tuple(range(count, count * 2))]
    faces.extend((i, (i + 1) % count, count + (i + 1) % count, count + i) for i in range(count))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    return mesh


def aim(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(scene, camera, path, location, target, lens, resolution):
    camera.location = location
    camera.data.lens = lens
    aim(camera, target)
    scene.camera = camera
    scene.render.resolution_x, scene.render.resolution_y = resolution
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(path)}


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    for path in (STAGE, RENDERS, AUDIT.parent):
        path.mkdir(parents=True, exist_ok=True)

    source_points, smooth_points = contour_points()
    body = bpy.data.objects["V206_BODY_CORE"]
    material = body.active_material
    old_mesh = body.data
    body.data = prism_mesh("V343_SMOOTH_IMAGE_CONTOUR_BODY", smooth_points)
    bpy.data.meshes.remove(old_mesh)
    body.data.materials.append(material)
    for modifier in list(body.modifiers):
        body.modifiers.remove(modifier)
    bevel = body.modifiers.new("V343_BODY_EDGE_RADIUS", "BEVEL")
    bevel.width = .006
    bevel.segments = 6

    principled = material.node_tree.nodes.get("Principled BSDF")
    principled.inputs["Base Color"].default_value = (.008, .012, .017, 1)
    principled.inputs["Metallic"].default_value = .12
    principled.inputs["Roughness"].default_value = .43
    bump = material.node_tree.nodes.get("Bump")
    if bump:
        bump.inputs["Strength"].default_value = .035
        bump.inputs["Distance"].default_value = .00035

    disabled_lights = []
    for obj in bpy.context.scene.objects:
        if obj.type == "LIGHT" and (obj.name.startswith("V322_") or obj.name.startswith("V206_")):
            obj.hide_render = True
            obj.hide_viewport = True
            disabled_lights.append(obj.name)

    scene = bpy.context.scene
    scene["V343_STATUS"] = "GUITAR_SURFACE_REFINEMENT_VISUAL_REVIEW_REQUIRED"
    camera = bpy.data.objects["V323_CAMERA"]
    renders = {
        "full_front": render(scene, camera, RENDERS / "v343_full_front.png", (.18, -3.75, 1.10), (.10, -.10, 1.08), 67, (1000, 1200)),
        "guitar_beauty": render(scene, camera, RENDERS / "v343_guitar_beauty.png", (1.25, -2.25, 1.42), (.33, -.30, 1.35), 82, (1100, 900)),
        "guitar_front": render(scene, camera, RENDERS / "v343_guitar_front.png", (.68, -2.25, 1.46), (.34, -.30, 1.34), 96, (900, 1000)),
    }
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v343-guitar-surface-refinement-v1",
        "status": "BUILT_VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)},
        "contour_points": {"source": len(source_points), "smoothed": len(smooth_points)},
        "disabled_duplicate_lights": disabled_lights,
        "renders": renders,
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha(OUTPUT)},
    }
    AUDIT.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V343_GUITAR_REFINEMENT_OK=" + json.dumps(record["output"], sort_keys=True))


if __name__ == "__main__":
    main()
