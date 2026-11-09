"""Replace the coarse V206 body polygon with a product-reference silhouette."""

from pathlib import Path
import hashlib
import json

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v294_pick_string_alignment" / "Character_An_pick_string_alignment_v294.blend"
OUTLINE = ROOT / "production_v298_reference_guitar_body" / "analysis" / "strandberg_body_outline.json"
STAGE = ROOT / "production_v298_reference_guitar_body"
OUTPUT = STAGE / "Character_An_reference_guitar_body_v298.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            digest.update(block)
    return digest.hexdigest()


def point_at(obj, target):
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
    modifier = obj.modifiers.new("V298_ROUNDED_BODY_EDGE", "BEVEL")
    modifier.width = bevel
    modifier.segments = 5
    modifier.limit_method = "ANGLE"
    return obj


def figured_material():
    material = bpy.data.materials.get("MAT_V298_SMOKY_QUILT_MAPLE") or bpy.data.materials.new("MAT_V298_SMOKY_QUILT_MAPLE")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    surface = nodes.new("ShaderNodeBsdfPrincipled")
    texcoord = nodes.new("ShaderNodeTexCoord")
    mapping = nodes.new("ShaderNodeMapping")
    wave = nodes.new("ShaderNodeTexWave")
    noise = nodes.new("ShaderNodeTexNoise")
    mix = nodes.new("ShaderNodeMixRGB")
    ramp = nodes.new("ShaderNodeValToRGB")
    bump = nodes.new("ShaderNodeBump")
    mapping.inputs["Scale"].default_value = (1.2, 2.2, 1.0)
    wave.wave_type = "BANDS"
    wave.bands_direction = "X"
    wave.inputs["Scale"].default_value = 34.0
    wave.inputs["Distortion"].default_value = 7.5
    wave.inputs["Detail"].default_value = 5.0
    noise.inputs["Scale"].default_value = 4.2
    noise.inputs["Detail"].default_value = 7.0
    noise.inputs["Roughness"].default_value = .64
    mix.blend_type = "MULTIPLY"
    mix.inputs[0].default_value = .62
    ramp.color_ramp.elements[0].position = .16
    ramp.color_ramp.elements[0].color = (.004, .005, .006, 1.0)
    ramp.color_ramp.elements[1].position = .84
    ramp.color_ramp.elements[1].color = (.18, .205, .205, 1.0)
    surface.inputs["Roughness"].default_value = .27
    surface.inputs["Coat Weight"].default_value = .26
    surface.inputs["Coat Roughness"].default_value = .22
    bump.inputs["Strength"].default_value = .11
    bump.inputs["Distance"].default_value = .0003
    links.new(texcoord.outputs["Generated"], mapping.inputs["Vector"])
    links.new(mapping.outputs["Vector"], wave.inputs["Vector"])
    links.new(mapping.outputs["Vector"], noise.inputs["Vector"])
    links.new(wave.outputs["Color"], mix.inputs[1])
    links.new(noise.outputs["Fac"], mix.inputs[2])
    links.new(mix.outputs["Color"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], surface.inputs["Base Color"])
    links.new(mix.outputs["Color"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], surface.inputs["Normal"])
    links.new(surface.outputs["BSDF"], output.inputs["Surface"])
    return material


def render(scene, camera, path, location, target, lens, resolution):
    camera.location = location
    camera.data.lens = lens
    point_at(camera, target)
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
    outline_record = json.loads(OUTLINE.read_text())
    points = [tuple(item) for item in outline_record["points"]]
    root = bpy.data.objects["V206_GUITAR_ROOT"]
    old = {}
    for name in ("V206_BODY_CORE", "V206_FIGURED_TOP"):
        obj = bpy.data.objects.get(name)
        if obj:
            old[name] = {"vertices": len(obj.data.vertices), "sha_hint": obj.data.name}
            bpy.data.objects.remove(obj, do_unlink=True)
    edge = bpy.data.materials["MAT_V206_BODY_EDGE"]
    top_material = figured_material()
    body = extruded("V206_BODY_CORE", points, -.047, -.003, edge, .009)
    body.parent = root
    body["construction"] = "product_reference_dense_asymmetric_double_cut"
    center = Vector((sum(x for x, _y in points) / len(points), sum(y for _x, y in points) / len(points)))
    top_points = [
        (center.x + (x - center.x) * .985, center.y + (y - center.y) * .978)
        for x, y in points
    ]
    top = extruded("V206_FIGURED_TOP", top_points, -.003, .005, top_material, .004)
    top.parent = root
    top["finish"] = "smoky_charcoal_quilted_maple_satin"
    bpy.context.view_layer.update()

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.look = "AgX - Medium High Contrast"
    camera = bpy.data.objects["V287_GUITAR_CAMERA"]
    renders = {}
    renders["full"] = render(
        scene, camera, RENDERS / "v298_full.png",
        Vector((0.0, -3.75, 1.02)), Vector((0.0, -.02, 1.0)), 66.0, (900, 1000),
    )
    guitar_center = root.matrix_world @ Vector((.70, 0.0, -.01))
    guitar_front = root.matrix_world @ Vector((.70, 0.0, 1.42))
    renders["guitar_front"] = render(
        scene, camera, RENDERS / "v298_guitar_front.png",
        guitar_front, guitar_center, 82.0, (1100, 900),
    )
    guitar_beauty = root.matrix_world @ Vector((.72, -.62, 1.18))
    renders["guitar_beauty"] = render(
        scene, camera, RENDERS / "v298_guitar_beauty.png",
        guitar_beauty, guitar_center, 86.0, (1100, 900),
    )
    scene["V298_STATUS"] = "REFERENCE_BODY_VISUAL_REVIEW_REQUIRED"
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v298-reference-guitar-body-v1",
        "status": "VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)},
        "outline": {"path": str(OUTLINE.relative_to(ROOT)), "points": len(points), "sha256": sha(OUTLINE)},
        "replaced": old,
        "body": {"vertices": len(body.data.vertices), "faces": len(body.data.polygons)},
        "renders": renders,
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha(OUTPUT)},
    }
    (AUDIT / "v298_reference_guitar_body.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V298_REFERENCE_GUITAR_BODY_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
