"""Render CharMorph male sources at body and hand scale before integration."""

from pathlib import Path
import hashlib
import json

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
DATA = ROOT / "third_party" / "charmorph" / "v0.4.0-3" / "CharMorph-data" / "characters"
STAGE = ROOT / "production_v306_charmorph_source_validation"
OUTPUT = STAGE / "Character_An_charmorph_sources_v306.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            digest.update(block)
    return digest.hexdigest()


def material():
    mat = bpy.data.materials.new("V306_SOURCE_CLAY")
    mat.diffuse_color = (.36, .16, .09, 1.0)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (.30, .105, .055, 1.0)
    bsdf.inputs["Roughness"].default_value = .48
    bsdf.inputs["Subsurface Weight"].default_value = .05
    return mat


def append_mesh(candidate):
    blend = DATA / candidate / "char.blend"
    with bpy.data.libraries.load(str(blend), link=False) as (source, target):
        target.objects = list(source.objects)
    meshes = [obj for obj in target.objects if obj and obj.type == "MESH" and len(obj.data.vertices) > 1000]
    source_name = {"mb_male": "mb_male", "reom": "cm_reom"}[candidate]
    obj = next(item for item in meshes if item.name == source_name)
    obj.name = f"V306_{candidate.upper()}"
    bpy.context.collection.objects.link(obj)
    return obj, blend


def camera_at(camera, location, target, lens):
    camera.location = location
    camera.data.lens = lens
    camera.rotation_euler = (target - location).to_track_quat("-Z", "Y").to_euler()


def render(scene, path):
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(path)}


def hand_bbox(obj, positive=True):
    world_points = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
    xs = [point.x for point in world_points]
    threshold = (max(xs) - .19) if positive else (min(xs) + .19)
    points = [point for point in world_points if (point.x >= threshold if positive else point.x <= threshold)]
    lo = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
    hi = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
    return lo, hi, (lo + hi) * .5, len(points)


def main():
    bpy.ops.wm.read_homefile(use_empty=True, use_factory_startup=True)
    for folder in (STAGE, RENDERS, AUDIT):
        folder.mkdir(parents=True, exist_ok=True)
    clay = material()
    candidates = {}
    for candidate in ("mb_male", "reom"):
        obj, path = append_mesh(candidate)
        obj.data.materials.clear()
        obj.data.materials.append(clay)
        for polygon in obj.data.polygons:
            polygon.material_index = 0
            polygon.use_smooth = True
        if candidate == "reom":
            subdiv = obj.modifiers.new("V306_SOURCE_SUBDIVISION", "SUBSURF")
            subdiv.levels = 2
            subdiv.render_levels = 2
        candidates[candidate] = (obj, path)

    camera_data = bpy.data.cameras.new("V306_CAMERA")
    camera = bpy.data.objects.new("V306_CAMERA", camera_data)
    bpy.context.collection.objects.link(camera)
    scene = bpy.context.scene
    scene.camera = camera
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.world = bpy.data.worlds.new("V306_WORLD")
    scene.world.color = (.008, .008, .012)
    for name, location, energy, size in (
        ("KEY", (-2.5, -3.0, 4.0), 1200, 3.0),
        ("FILL", (2.8, -1.8, 2.5), 850, 2.5),
        ("RIM", (0.0, 2.2, 3.2), 1000, 2.0),
    ):
        data = bpy.data.lights.new(f"V306_{name}", "AREA")
        data.energy = energy
        data.shape = "DISK"
        data.size = size
        light = bpy.data.objects.new(f"V306_{name}", data)
        light.location = location
        bpy.context.collection.objects.link(light)

    renders = {}
    audit = {}
    for candidate, (obj, path) in candidates.items():
        for other, (other_obj, _other_path) in candidates.items():
            other_obj.hide_render = other != candidate
        scene.render.resolution_x = 900
        scene.render.resolution_y = 1100
        world_bbox = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
        body_lo = Vector((min(p.x for p in world_bbox), min(p.y for p in world_bbox), min(p.z for p in world_bbox)))
        body_hi = Vector((max(p.x for p in world_bbox), max(p.y for p in world_bbox), max(p.z for p in world_bbox)))
        center = (body_lo + body_hi) * .5
        camera_at(camera, center + Vector((0, -3.3, .02)), center, 72)
        renders[f"{candidate}_body"] = render(scene, RENDERS / f"v306_{candidate}_body.png")

        lo, hi, hand_center, count = hand_bbox(obj, positive=True)
        extent = max((hi - lo).x, (hi - lo).y, (hi - lo).z)
        scene.render.resolution_x = 1100
        scene.render.resolution_y = 900
        camera_at(camera, hand_center + Vector((0, -max(.48, extent * 3.2), .025)), hand_center, 92)
        renders[f"{candidate}_hand_front"] = render(scene, RENDERS / f"v306_{candidate}_hand_front.png")
        camera_at(camera, hand_center + Vector((max(.20, extent * 1.15), -max(.40, extent * 2.7), .10)), hand_center, 92)
        renders[f"{candidate}_hand_oblique"] = render(scene, RENDERS / f"v306_{candidate}_hand_oblique.png")
        audit[candidate] = {
            "source": str(path.relative_to(ROOT)),
            "vertices": len(obj.data.vertices),
            "polygons": len(obj.data.polygons),
            "hand_region_vertices": count,
            "hand_bbox_min": list(lo),
            "hand_bbox_max": list(hi),
        }

    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v306-charmorph-source-validation-v1",
        "status": "VISUAL_REVIEW_REQUIRED",
        "candidates": audit,
        "renders": renders,
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha(OUTPUT)},
    }
    (AUDIT / "v306_charmorph_source_validation.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V306_CHARMORPH_SOURCE_VALIDATION_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
