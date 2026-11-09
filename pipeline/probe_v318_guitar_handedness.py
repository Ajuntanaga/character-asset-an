"""Render both outline handedness candidates against the live character pose."""

from pathlib import Path
import hashlib
import json

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v316_identity_reactivation" / "Character_An_identity_reactivation_v316.blend"
OUTLINE = ROOT / "production_v298_reference_guitar_body" / "analysis" / "strandberg_body_outline.json"
STAGE = ROOT / "production_v318_reference_guitar_rebuild"
RENDERS = STAGE / "renders" / "handedness_probe"
AUDIT = STAGE / "audit"


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            digest.update(block)
    return digest.hexdigest()


def aim(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def extruded(name, points, z_bottom, z_top, material, bevel):
    count = len(points)
    vertices = [(x, y, z_bottom) for x, y in points] + [(x, y, z_top) for x, y in points]
    faces = [tuple(reversed(range(count))), tuple(range(count, count * 2))]
    faces.extend((index, (index + 1) % count, count + (index + 1) % count, count + index) for index in range(count))
    mesh = bpy.data.meshes.new(name + "_MESH")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    mesh.materials.append(material)
    modifier = obj.modifiers.new("V318_PROBE_EDGE", "BEVEL")
    modifier.width = bevel
    modifier.segments = 5
    modifier.limit_method = "ANGLE"
    return obj


def material(name, color, roughness):
    value = bpy.data.materials.new(name)
    value.use_nodes = True
    shader = value.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = color
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Coat Weight"].default_value = 0.12
    return value


def render(scene, camera, path, location, target, lens):
    camera.location = location
    camera.data.lens = lens
    aim(camera, target)
    scene.camera = camera
    scene.render.resolution_x = 1100
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(path)}


def candidate(label, mirror):
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    root = bpy.data.objects["V206_GUITAR_ROOT"]
    record = json.loads(OUTLINE.read_text())
    points = [tuple(item) for item in record["points"]]
    if mirror:
        points = [(x, -y) for x, y in reversed(points)]
    for name in ("V206_BODY_CORE", "V206_FIGURED_TOP"):
        obj = bpy.data.objects.get(name)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)
    edge = material(f"V318_PROBE_EDGE_{label}", (0.010, 0.012, 0.014, 1.0), 0.42)
    top_material = material(f"V318_PROBE_TOP_{label}", (0.10, 0.115, 0.12, 1.0), 0.34)
    body = extruded("V206_BODY_CORE", points, -0.040, -0.003, edge, 0.005)
    body.parent = root
    center = Vector((sum(x for x, _y in points) / len(points), sum(y for _x, y in points) / len(points)))
    top_points = [(center.x + (x - center.x) * 0.990, center.y + (y - center.y) * 0.986) for x, y in points]
    top = extruded("V206_FIGURED_TOP", top_points, -0.003, 0.004, top_material, 0.0025)
    top.parent = root
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.look = "AgX - Medium High Contrast"
    camera = bpy.data.objects["V287_GUITAR_CAMERA"]
    center_world = root.matrix_world @ Vector((0.70, 0.0, -0.01))
    front = render(
        scene, camera, RENDERS / f"v318_{label}_front.png",
        root.matrix_world @ Vector((0.70, 0.0, 1.42)), center_world, 82.0,
    )
    beauty = render(
        scene, camera, RENDERS / f"v318_{label}_beauty.png",
        root.matrix_world @ Vector((0.72, -0.62, 1.18)), center_world, 86.0,
    )
    return {"mirror_local_y": mirror, "front": front, "beauty": beauty}


def main():
    RENDERS.mkdir(parents=True, exist_ok=True)
    AUDIT.mkdir(parents=True, exist_ok=True)
    candidates = {
        "as_traced": candidate("as_traced", False),
        "mirrored": candidate("mirrored", True),
    }
    record = {
        "schema": "v318-guitar-handedness-probe-v1",
        "status": "VISUAL_SELECTION_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)},
        "outline": {"path": str(OUTLINE.relative_to(ROOT)), "sha256": sha(OUTLINE)},
        "candidates": candidates,
    }
    (AUDIT / "v318_guitar_handedness_probe.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V318_GUITAR_HANDEDNESS_PROBE_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
