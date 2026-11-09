"""Rebuild the posed guitar body to the supplied Strandberg photo and dimensions."""

from pathlib import Path
import hashlib
import json
import math

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v316_identity_reactivation" / "Character_An_identity_reactivation_v316.blend"
OUTLINE = ROOT / "production_v318_reference_guitar_rebuild" / "analysis" / "strandberg_hybrid_outline.json"
STAGE = ROOT / "production_v318_reference_guitar_rebuild"
OUTPUT = STAGE / "Character_An_reference_guitar_rebuild_v318.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            digest.update(block)
    return digest.hexdigest()


def remove_charmorph_handlers():
    removed = []
    for handler in list(bpy.app.handlers.depsgraph_update_post):
        if getattr(handler, "__module__", "").startswith("CharMorph"):
            bpy.app.handlers.depsgraph_update_post.remove(handler)
            removed.append(f"{handler.__module__}.{handler.__name__}")
    return removed


def aim(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def extruded(name, points, z_bottom, z_top, material, bevel, collection):
    count = len(points)
    vertices = [(x, y, z_bottom) for x, y in points] + [(x, y, z_top) for x, y in points]
    faces = [tuple(reversed(range(count))), tuple(range(count, count * 2))]
    faces.extend((index, (index + 1) % count, count + (index + 1) % count, count + index) for index in range(count))
    mesh = bpy.data.meshes.new(name + "_MESH")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    mesh.materials.append(material)
    modifier = obj.modifiers.new("V318_PHYSICAL_EDGE_ROLL", "BEVEL")
    modifier.width = bevel
    modifier.segments = 6
    modifier.limit_method = "ANGLE"
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    return obj


def simple_material(name, color, roughness, metallic=0.0):
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    surface = nodes.new("ShaderNodeBsdfPrincipled")
    surface.inputs["Base Color"].default_value = color
    surface.inputs["Roughness"].default_value = roughness
    surface.inputs["Metallic"].default_value = metallic
    surface.inputs["Coat Weight"].default_value = 0.16
    surface.inputs["Coat Roughness"].default_value = 0.22
    links.new(surface.outputs["BSDF"], output.inputs["Surface"])
    return material


def figured_material():
    material = bpy.data.materials.get("MAT_V318_SMOKY_FLAME_MAPLE") or bpy.data.materials.new("MAT_V318_SMOKY_FLAME_MAPLE")
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
    multiply = nodes.new("ShaderNodeMixRGB")
    ramp = nodes.new("ShaderNodeValToRGB")
    bump = nodes.new("ShaderNodeBump")

    mapping.inputs["Scale"].default_value = (1.0, 1.0, 1.0)
    wave.wave_type = "BANDS"
    wave.bands_direction = "X"
    wave.inputs["Scale"].default_value = 11.5
    wave.inputs["Distortion"].default_value = 4.2
    wave.inputs["Detail"].default_value = 3.8
    wave.inputs["Detail Scale"].default_value = 1.8
    noise.inputs["Scale"].default_value = 3.2
    noise.inputs["Detail"].default_value = 4.0
    noise.inputs["Roughness"].default_value = 0.52
    multiply.blend_type = "MULTIPLY"
    multiply.inputs[0].default_value = 0.72
    ramp.color_ramp.elements.remove(ramp.color_ramp.elements[1])
    dark = ramp.color_ramp.elements[0]
    dark.position = 0.12
    dark.color = (0.010, 0.013, 0.014, 1.0)
    mid = ramp.color_ramp.elements.new(0.48)
    mid.color = (0.022, 0.028, 0.029, 1.0)
    light = ramp.color_ramp.elements.new(0.82)
    light.color = (0.042, 0.052, 0.052, 1.0)
    surface.inputs["Roughness"].default_value = 0.29
    surface.inputs["Coat Weight"].default_value = 0.31
    surface.inputs["Coat Roughness"].default_value = 0.18
    bump.inputs["Strength"].default_value = 0.022
    bump.inputs["Distance"].default_value = 0.00008

    links.new(texcoord.outputs["Generated"], mapping.inputs["Vector"])
    links.new(mapping.outputs["Vector"], wave.inputs["Vector"])
    links.new(mapping.outputs["Vector"], noise.inputs["Vector"])
    links.new(wave.outputs["Color"], multiply.inputs[1])
    links.new(noise.outputs["Fac"], multiply.inputs[2])
    links.new(multiply.outputs["Color"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], surface.inputs["Base Color"])
    links.new(multiply.outputs["Color"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], surface.inputs["Normal"])
    links.new(surface.outputs["BSDF"], output.inputs["Surface"])
    return material


def inset(points, x_scale, y_scale):
    center = Vector((sum(x for x, _y in points) / len(points), sum(y for _x, y in points) / len(points)))
    return [(center.x + (x - center.x) * x_scale, center.y + (y - center.y) * y_scale) for x, y in points]


def local_xy(obj, x, y, z=None):
    obj.location.x = x
    obj.location.y = y
    if z is not None:
        obj.location.z = z


def configure_pickup(prefix, x, angle_degrees):
    pickup = bpy.data.objects[f"V206_PICKUP_{prefix}"]
    pickup.location = (x, 0.0, 0.015)
    pickup.rotation_euler = (0.0, 0.0, math.radians(angle_degrees))
    angle = math.radians(angle_degrees)
    for index, offset in enumerate((-0.041, 0.041), 1):
        screw = bpy.data.objects.get(f"V206_{prefix}_MOUNT_SCREW_{index}")
        if screw:
            screw.location = (x - math.sin(angle) * offset, math.cos(angle) * offset, 0.0228)
    return {"x_m": x, "angle_degrees": angle_degrees}


def configure_controls():
    positions = {
        "V206_CONTROL_KNOB_1": (0.702, -0.056, 0.020),
        "V206_CONTROL_KNOB_2": (0.694, -0.112, 0.020),
        "V206_CONTROL_SWITCH_BASE": (0.615, -0.078, 0.015),
    }
    for name, position in positions.items():
        obj = bpy.data.objects.get(name)
        if obj:
            obj.location = position
    toggle = bpy.data.objects.get("V206_CONTROL_SWITCH_TOGGLE")
    if toggle and toggle.type == "CURVE":
        # Curve points are stored in guitar-local coordinates.
        spline = toggle.data.splines[0]
        spline.points[0].co = (0.615, -0.078, 0.020, 1.0)
        spline.points[1].co = (0.624, -0.078, 0.043, 1.0)
    jack = bpy.data.objects.get("V206_OUTPUT_JACK")
    if jack:
        jack.location = (0.794, -0.132, -0.002)
    for name, position in {
        "V206_STRAP_BUTTON_1": (0.842, 0.090, -0.020),
        "V206_STRAP_BUTTON_2": (0.790, -0.145, -0.020),
    }.items():
        obj = bpy.data.objects.get(name)
        if obj:
            obj.location = position
    return positions


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
    removed_handlers = remove_charmorph_handlers()
    for folder in (STAGE, RENDERS, AUDIT):
        folder.mkdir(parents=True, exist_ok=True)
    outline_record = json.loads(OUTLINE.read_text())
    points = [tuple(item) for item in outline_record["points"]]
    width = max(y for _x, y in points) - min(y for _x, y in points)
    farthest_x = max(x for x, _y in points)
    if abs(width - 0.330) > 0.003:
        raise RuntimeError(f"V318 body width is not the official 330 mm envelope: {width}")
    if abs(farthest_x - 0.850) > 0.004:
        raise RuntimeError(f"V318 body end is not the official 850 mm envelope: {farthest_x}")

    root = bpy.data.objects["V206_GUITAR_ROOT"]
    collections = list(bpy.data.objects["V206_BODY_CORE"].users_collection)
    collection = collections[0] if collections else bpy.context.scene.collection
    removed = []
    for name in ("V206_BODY_CORE", "V206_FIGURED_TOP", "V318_BODY_REVEAL"):
        obj = bpy.data.objects.get(name)
        if obj:
            removed.append(name)
            bpy.data.objects.remove(obj, do_unlink=True)
    for obj in list(bpy.data.objects):
        if obj.name.startswith(("V206_NECK_POLE_", "V206_BRIDGE_POLE_")):
            removed.append(obj.name)
            bpy.data.objects.remove(obj, do_unlink=True)

    edge = simple_material("MAT_V318_CHARCOAL_BODY_EDGE", (0.006, 0.008, 0.009, 1.0), 0.34)
    reveal_material = simple_material("MAT_V318_MAPLE_REVEAL", (0.030, 0.020, 0.010, 1.0), 0.33)
    top_material = figured_material()
    body = extruded("V206_BODY_CORE", points, -0.037, -0.003, edge, 0.0048, collection)
    body.parent = root
    body["construction"] = "official_scale_330mm_reference_traced_boden_8_body"
    reveal_points = inset(points, 0.992, 0.989)
    reveal = extruded("V318_BODY_REVEAL", reveal_points, -0.003, 0.001, reveal_material, 0.0022, collection)
    reveal.parent = root
    top_points = inset(points, 0.984, 0.979)
    top = extruded("V206_FIGURED_TOP", top_points, 0.001, 0.005, top_material, 0.0026, collection)
    top.parent = root
    top["finish"] = "smoky_black_granite_flame_maple_satin"

    pickups = {
        "neck": configure_pickup("NECK", 0.575, -8.0),
        "bridge": configure_pickup("BRIDGE", 0.655, -12.0),
    }
    controls = configure_controls()
    root["body_width_m"] = width
    root["body_end_from_nut_m"] = farthest_x
    root["body_thickness_m"] = 0.042
    root["official_instrument_length_m"] = 0.850
    root["official_instrument_width_m"] = 0.330
    root["reference_model"] = "Strandberg Boden 8"

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.look = "AgX - Medium High Contrast"
    camera = bpy.data.objects.get("V287_GUITAR_CAMERA") or bpy.data.objects["V316_PORTRAIT_CAMERA"]
    guitar_center = root.matrix_world @ Vector((0.62, 0.0, -0.006))
    renders = {
        "guitar_front": render(
            scene, camera, RENDERS / "v318_guitar_front.png",
            root.matrix_world @ Vector((0.62, 0.0, 1.28)), guitar_center, 86.0, (1200, 1000),
        ),
        "guitar_beauty": render(
            scene, camera, RENDERS / "v318_guitar_beauty.png",
            root.matrix_world @ Vector((0.64, -0.53, 1.05)), guitar_center, 90.0, (1200, 1000),
        ),
        "full_character": render(
            scene, camera, RENDERS / "v318_full_character.png",
            Vector((0.0, -3.75, 1.02)), Vector((0.0, -0.02, 1.0)), 66.0, (900, 1000),
        ),
    }
    scene["V318_STATUS"] = "OFFICIAL_SCALE_REFERENCE_BODY_BUILT_VISUAL_REVIEW_REQUIRED"
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v318-reference-guitar-rebuild-v1",
        "status": "BUILT_VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)},
        "outline": {"path": str(OUTLINE.relative_to(ROOT)), "sha256": sha(OUTLINE), "points": len(points)},
        "official_dimensions_m": {"width": 0.330, "instrument_length": 0.850, "body_thickness": 0.042},
        "measured_geometry_m": {"body_width": width, "body_end_from_nut": farthest_x},
        "pickups": pickups,
        "controls": controls,
        "removed_objects": sorted(removed),
        "removed_session_handlers": removed_handlers,
        "renders": renders,
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha(OUTPUT)},
    }
    (AUDIT / "v318_reference_guitar_rebuild.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V318_REFERENCE_GUITAR_REBUILD_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
