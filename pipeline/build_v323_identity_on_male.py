"""Fit the accepted FaceBuilder identity assembly to the corrected male rig."""

from pathlib import Path
import hashlib
import json
import math

import bpy
from mathutils import Matrix, Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v322_character_rebuild" / "Character_An_mb_male_rig_v322.blend"
IDENTITY_SOURCE = ROOT / "production_v316_identity_reactivation" / "Character_An_identity_reactivation_v316.blend"
STAGE = ROOT / "production_v323_identity_on_male"
OUTPUT = STAGE / "Character_An_identity_on_male_v323.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit" / "v323_identity_on_male.json"
BODY = "V322_MB_MALE_BODY"
RIG = "V322_MB_MALE_RIG"
SOURCE_RIG = "V310_REOM_RIG"
HEAD = "V216_REFERENCE_FITTED_HEAD"
IDENTITY_OBJECTS = (
    HEAD,
    "V216_EYE_L", "V216_EYE_R",
    "V216_IRIS_L", "V216_IRIS_R",
    "V216_PUPIL_L", "V216_PUPIL_R",
    "V217_TIGHT_CURL_GROOM",
)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            digest.update(block)
    return digest.hexdigest()


def aim(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def world_bounds(obj):
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    lower = Vector(tuple(min(point[axis] for point in points) for axis in range(3)))
    upper = Vector(tuple(max(point[axis] for point in points) for axis in range(3)))
    return lower, upper


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


def append_identity():
    names = list(IDENTITY_OBJECTS) + [SOURCE_RIG]
    with bpy.data.libraries.load(str(IDENTITY_SOURCE), link=False) as (source, target):
        missing = [name for name in names if name not in source.objects]
        if missing:
            raise RuntimeError(f"Identity source is missing {missing}")
        target.objects = names
    loaded = {obj.name: obj for obj in target.objects if obj is not None}
    for obj in loaded.values():
        if obj.name not in bpy.context.scene.collection.objects:
            bpy.context.scene.collection.objects.link(obj)
    return loaded


def clear_parent_preserve_world(obj):
    world = obj.matrix_world.copy()
    obj.parent = None
    obj.matrix_parent_inverse.identity()
    obj.matrix_world = world
    for constraint in list(obj.constraints):
        obj.constraints.remove(constraint)


def parent_to_head(obj, rig):
    world = obj.matrix_world.copy()
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = "head"
    obj.matrix_world = world


def install_head_mask(body, cutoff):
    group = body.vertex_groups.get("V323_HIDE_MB_HEAD") or body.vertex_groups.new(name="V323_HIDE_MB_HEAD")
    selected = [
        vertex.index
        for vertex in body.data.vertices
        if (body.matrix_world @ vertex.co).z > cutoff
    ]
    group.add(selected, 1.0, "REPLACE")
    modifier = body.modifiers.get("V323_HIDE_MB_HEAD") or body.modifiers.new("V323_HIDE_MB_HEAD", "MASK")
    modifier.vertex_group = group.name
    modifier.invert_vertex_group = True
    body.modifiers.move(body.modifiers.find(modifier.name), 0)
    return {"cutoff_z_m": cutoff, "hidden_vertices": len(selected), "modifier": modifier.name}


def darken_groom(groom):
    touched = []
    for slot in groom.material_slots:
        material = slot.material
        if material is None or material.node_tree is None:
            continue
        material = material.copy()
        slot.material = material
        for node in material.node_tree.nodes:
            if node.type == "BSDF_HAIR_PRINCIPLED":
                if "Melanin" in node.inputs:
                    node.inputs["Melanin"].default_value = 0.88
                if "Melanin Redness" in node.inputs:
                    node.inputs["Melanin Redness"].default_value = 0.08
                if "Roughness" in node.inputs:
                    node.inputs["Roughness"].default_value = 0.42
                if "Coat" in node.inputs:
                    node.inputs["Coat"].default_value = 0.12
            elif node.type == "BSDF_PRINCIPLED":
                node.inputs["Base Color"].default_value = (0.0035, 0.0022, 0.0015, 1.0)
                node.inputs["Roughness"].default_value = 0.50
        touched.append(material.name)
    return touched


def add_poly_curve(name, points, material, bevel_depth, cyclic=False):
    data = bpy.data.curves.new(name + "_DATA", "CURVE")
    data.dimensions = "3D"
    data.resolution_u = 2
    data.bevel_depth = bevel_depth
    data.bevel_resolution = 3
    spline = data.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for point, co in zip(spline.points, points):
        point.co = (*co, 1.0)
    spline.use_cyclic_u = cyclic
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(material)
    return obj


def add_glasses(eyes, head_bounds):
    left = eyes["V216_EYE_L"].matrix_world.translation
    right = eyes["V216_EYE_R"].matrix_world.translation
    if left.x > right.x:
        left, right = right, left
    separation = right.x - left.x
    lens_width = separation * 0.79
    lens_height = lens_width * 0.72
    front_y = min(left.y, right.y) - lens_width * 0.25
    black = bpy.data.materials.new("V323_GLASSES_BLACK")
    black.use_nodes = True
    bsdf = black.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (0.004, 0.005, 0.006, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.29
    bsdf.inputs["Metallic"].default_value = 0.04
    frames = []
    for label, center in (("L", left), ("R", right)):
        points = [
            Vector((
                center.x + lens_width * 0.5 * math.cos(angle),
                front_y,
                center.z + lens_height * 0.5 * math.sin(angle),
            ))
            for angle in (2.0 * math.pi * i / 48 for i in range(48))
        ]
        frames.append(add_poly_curve(f"V323_GLASSES_FRAME_{label}", points, black, 0.00145, True))
    inner_left = left.x + lens_width * 0.5
    inner_right = right.x - lens_width * 0.5
    bridge_z = (left.z + right.z) * 0.5 + lens_height * 0.04
    bridge = add_poly_curve(
        "V323_GLASSES_BRIDGE",
        [Vector((inner_left, front_y, bridge_z)), Vector((inner_right, front_y, bridge_z))],
        black,
        0.00135,
    )
    outer_left = left.x - lens_width * 0.5
    outer_right = right.x + lens_width * 0.5
    back_y = head_bounds[1].y * 0.82 + front_y * 0.18
    temple_z = (left.z + right.z) * 0.5
    temples = [
        add_poly_curve("V323_GLASSES_TEMPLE_L", [Vector((outer_left, front_y, temple_z)), Vector((head_bounds[0].x * 0.92, back_y, temple_z - 0.006))], black, 0.00125),
        add_poly_curve("V323_GLASSES_TEMPLE_R", [Vector((outer_right, front_y, temple_z)), Vector((head_bounds[1].x * 0.92, back_y, temple_z - 0.006))], black, 0.00125),
    ]
    return frames + [bridge] + temples


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    for folder in (STAGE, RENDERS, AUDIT.parent):
        folder.mkdir(parents=True, exist_ok=True)
    body = bpy.data.objects[BODY]
    rig = bpy.data.objects[RIG]
    loaded = append_identity()
    source_rig = loaded[SOURCE_RIG]
    bpy.context.view_layer.update()

    source_head = loaded[HEAD]
    source_lo, source_hi = world_bounds(source_head)
    source_center = (source_lo + source_hi) * 0.5
    body_lo, body_hi = world_bounds(body)
    target_head_points = [
        body.matrix_world @ vertex.co
        for vertex in body.data.vertices
        if (body.matrix_world @ vertex.co).z > body_hi.z - 0.22
    ]
    target_lo = Vector(tuple(min(point[axis] for point in target_head_points) for axis in range(3)))
    target_hi = Vector(tuple(max(point[axis] for point in target_head_points) for axis in range(3)))
    scale_factor = (target_hi.x - target_lo.x) / (source_hi.x - source_lo.x)
    target_height = (source_hi.z - source_lo.z) * scale_factor
    target_center = Vector((
        (target_lo.x + target_hi.x) * 0.5,
        (target_lo.y + target_hi.y) * 0.5,
        body_hi.z - target_height * 0.5,
    ))
    transform = Matrix.Translation(target_center) @ Matrix.Scale(scale_factor, 4) @ Matrix.Translation(-source_center)

    for name in IDENTITY_OBJECTS:
        obj = loaded[name]
        clear_parent_preserve_world(obj)
        obj.matrix_world = transform @ obj.matrix_world
        obj.hide_render = False
        obj.hide_viewport = False
    bpy.context.view_layer.update()
    fitted_lo, fitted_hi = world_bounds(source_head)
    mask = install_head_mask(body, fitted_lo.z + 0.004)
    groom_materials = darken_groom(loaded["V217_TIGHT_CURL_GROOM"])

    glasses = add_glasses(loaded, (fitted_lo, fitted_hi))
    for obj in [loaded[name] for name in IDENTITY_OBJECTS] + glasses:
        parent_to_head(obj, rig)
    bpy.data.objects.remove(source_rig, do_unlink=True)

    shape_count = len(source_head.data.shape_keys.key_blocks) - 1 if source_head.data.shape_keys else 0
    if shape_count != 51:
        raise RuntimeError(f"Expected 51 FACS shapes, found {shape_count}")

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.world.color = (0.006, 0.008, 0.012)
    for name, location, energy, size, color in (
        ("KEY", (-1.6, -2.4, 2.8), 760.0, 1.6, (1.0, 0.91, 0.84)),
        ("FILL", (1.7, -1.2, 2.2), 330.0, 1.7, (0.76, 0.86, 1.0)),
        ("RIM", (0.3, 1.9, 2.6), 560.0, 1.2, (1.0, 0.78, 0.66)),
    ):
        data = bpy.data.lights.new(f"V323_{name}_DATA", "AREA")
        data.energy = energy
        data.size = size
        data.color = color
        light = bpy.data.objects.new(f"V323_{name}", data)
        scene.collection.objects.link(light)
        light.location = location
        aim(light, Vector((0.0, -0.04, 1.64)))
    camera_data = bpy.data.cameras.new("V323_CAMERA_DATA")
    camera = bpy.data.objects.new("V323_CAMERA", camera_data)
    scene.collection.objects.link(camera)
    target = Vector((0.0, -0.045, 1.65))
    renders = {
        "portrait_front": render(scene, camera, RENDERS / "v323_portrait_front.png", Vector((0.0, -1.28, 1.66)), target, 104.0, (900, 900)),
        "portrait_three_quarter": render(scene, camera, RENDERS / "v323_portrait_three_quarter.png", Vector((0.58, -1.16, 1.70)), target, 100.0, (900, 900)),
        "portrait_profile": render(scene, camera, RENDERS / "v323_portrait_profile.png", Vector((1.22, -0.03, 1.67)), target, 100.0, (900, 900)),
        "full_front": render(scene, camera, RENDERS / "v323_full_front.png", Vector((0.0, -3.55, 1.02)), Vector((0.0, 0.0, 1.0)), 68.0, (900, 1100)),
    }
    scene["V323_STATUS"] = "FITTED_IDENTITY_ON_CORRECTED_MALE_VISUAL_REVIEW_REQUIRED"
    scene["V323_FACS_COUNT"] = shape_count
    scene["V323_IDENTITY_SCALE"] = scale_factor
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v323-identity-on-male-v1",
        "status": "BUILT_VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)},
        "identity_source": {"path": str(IDENTITY_SOURCE.relative_to(ROOT)), "sha256": sha(IDENTITY_SOURCE)},
        "identity_scale": scale_factor,
        "source_head_bounds_m": {"min": list(source_lo), "max": list(source_hi)},
        "target_head_bounds_m": {"min": list(target_lo), "max": list(target_hi)},
        "fitted_head_bounds_m": {"min": list(fitted_lo), "max": list(fitted_hi)},
        "head_mask": mask,
        "facs_count": shape_count,
        "groom_materials": groom_materials,
        "glasses": [obj.name for obj in glasses],
        "renders": renders,
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha(OUTPUT)},
    }
    AUDIT.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V323_IDENTITY_ON_MALE_OK=" + json.dumps({
        "identity_scale": scale_factor,
        "facs_count": shape_count,
        "mask_vertices": mask["hidden_vertices"],
        "output_sha256": record["output"]["sha256"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
