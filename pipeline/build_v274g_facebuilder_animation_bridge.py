"""Drive the reference-fitted FaceBuilder head with the V276 animation head."""

from pathlib import Path
import hashlib
import json
import math

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v276j_corrected_facial_controls" / "Character_An_corrected_facial_controls_v276j.blend"
DONOR_BLEND = ROOT / "production_v240_identity_clean_rig" / "Character_An_identity_clean_rig_v240.blend"
STAGE = ROOT / "production_v274g_facebuilder_animation_bridge"
OUTPUT = STAGE / "Character_An_facebuilder_animation_bridge_v274g.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"
DRIVER = "V276E_GEO-head_animation_realistic"
DONOR = "V216_REFERENCE_FITTED_HEAD"


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            digest.update(block)
    return digest.hexdigest()


def point_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def append_objects(names):
    with bpy.data.libraries.load(str(DONOR_BLEND), link=False) as (source, target):
        target.objects = [name for name in names if name in source.objects and name not in bpy.data.objects]
    for obj in target.objects:
        if obj and obj.name not in bpy.context.scene.collection.objects:
            bpy.context.scene.collection.objects.link(obj)


def transfer_expression_shapes(driver, donor):
    keys = driver.data.shape_keys.key_blocks
    identity = keys["IDENTITY_LANDMARK_WARP"]
    matrix = driver.matrix_world
    target_vertices = [matrix @ point.co for point in identity.data]
    polygons = [list(polygon.vertices) for polygon in driver.data.polygons]
    bvh = BVHTree.FromPolygons(target_vertices, polygons, all_triangles=False)
    donor_inverse = donor.matrix_world.inverted()
    mappings = []
    distances = []
    for vertex in donor.data.vertices:
        world = donor.matrix_world @ vertex.co
        location, _normal, polygon_index, distance = bvh.find_nearest(world)
        if location is None:
            raise RuntimeError(f"No target surface for donor vertex {vertex.index}")
        indices = polygons[polygon_index]
        raw = []
        for index in indices:
            d = (target_vertices[index] - location).length
            raw.append(1.0 / max(1e-8, d * d))
        total = sum(raw)
        weights = [value / total for value in raw]
        mappings.append((indices, weights, distance))
        distances.append(distance)

    if donor.data.shape_keys:
        while donor.data.shape_keys and len(donor.data.shape_keys.key_blocks):
            donor.shape_key_remove(donor.data.shape_keys.key_blocks[-1])
    basis = donor.shape_key_add(name="Basis", from_mix=False)
    driver_keys = [key for key in keys if key.name.startswith("CTRL_")]
    shape_records = {}
    for source_key in driver_keys:
        target_key = donor.shape_key_add(name=source_key.name, from_mix=False)
        target_key.relative_key = basis
        moved = 0
        maximum = 0.0
        for vertex, point, mapping in zip(donor.data.vertices, target_key.data, mappings):
            indices, weights, distance = mapping
            displacement = Vector()
            for index, weight in zip(indices, weights):
                displacement += (matrix @ source_key.data[index].co - target_vertices[index]) * weight
            attenuation = max(0.0, min(1.0, 1.0 - distance / 0.055))
            displacement *= attenuation
            if displacement.length > 1e-7:
                point.co = donor_inverse @ (donor.matrix_world @ vertex.co + displacement)
                moved += 1
                maximum = max(maximum, displacement.length)
        target_key.value = 0.0
        curve = target_key.driver_add("value")
        variable = curve.driver.variables.new()
        variable.name = "source"
        variable.type = "SINGLE_PROP"
        variable.targets[0].id_type = "KEY"
        variable.targets[0].id = driver.data.shape_keys
        variable.targets[0].data_path = f'key_blocks["{source_key.name}"].value'
        curve.driver.expression = "source"
        shape_records[source_key.name] = {"moved_vertices": moved, "max_displacement_m": maximum}
    return shape_records, {
        "mean_distance_m": sum(distances) / len(distances),
        "max_distance_m": max(distances),
        "mapped_vertices": len(mappings),
    }


def main():
    if Path(bpy.data.filepath).resolve() != SOURCE.resolve():
        bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    for folder in (STAGE, RENDERS, AUDIT):
        folder.mkdir(parents=True, exist_ok=True)

    required = [DONOR, "V216_EYE_L", "V216_EYE_R", "V217_TIGHT_CURL_GROOM", "V217_BEARD_STUBBLE", "V217_BROWS"]
    append_objects(required)
    driver = bpy.data.objects[DRIVER]
    donor = bpy.data.objects[DONOR]
    donor.hide_viewport = False
    donor.hide_render = False
    driver.hide_render = True

    # Clear the donor's old rig parenting while preserving its world-space fit.
    donor_world = donor.matrix_world.copy()
    donor.parent = None
    donor.matrix_world = donor_world
    for modifier in list(donor.modifiers):
        donor.modifiers.remove(modifier)
    shape_records, mapping_record = transfer_expression_shapes(driver, donor)
    donor_world = donor.matrix_world.copy()
    donor.parent = driver
    donor.matrix_parent_inverse = driver.matrix_world.inverted()
    donor.matrix_world = donor_world

    for side in ("L", "R"):
        donor_eye = bpy.data.objects[f"V216_EYE_{side}"]
        donor_eye.hide_viewport = False
        donor_eye.hide_render = False
        eye_world = donor_eye.matrix_world.copy()
        donor_eye.parent = None
        donor_eye.matrix_world = eye_world
        for constraint in list(donor_eye.constraints):
            donor_eye.constraints.remove(constraint)
        constraint = donor_eye.constraints.new("COPY_ROTATION")
        constraint.name = "V274G_GAZE_COPY"
        constraint.target = bpy.data.objects[f"V276E_GEO-head_animation_realistic.sclera.{side}"]
        constraint.owner_space = "WORLD"
        constraint.target_space = "WORLD"
        bpy.data.objects[f"V276E_GEO-head_animation_realistic.sclera.{side}"].hide_render = True
        bpy.data.objects[f"V276E_GEO-head_animation_realistic.iris.{side}"].hide_render = True

    groom_names = ["V217_TIGHT_CURL_GROOM", "V217_BEARD_STUBBLE", "V217_BROWS"]
    for name in groom_names:
        obj = bpy.data.objects[name]
        obj.hide_viewport = False
        obj.hide_render = False
        world = obj.matrix_world.copy()
        obj.parent = None
        obj.matrix_world = world
        obj.parent = donor
        obj.matrix_parent_inverse = donor.matrix_world.inverted()

    # Keep only the donor identity stack visible for the portrait proof.
    allowed = {DONOR, "V216_EYE_L", "V216_EYE_R", *groom_names}
    for obj in bpy.data.objects:
        if obj.type in {"MESH", "CURVE"} and obj.name not in allowed:
            obj.hide_render = True

    # Preserve the packed 4K identity texture, but make the shader physically calmer.
    material = donor.data.materials[0]
    if material and material.use_nodes:
        shader = material.node_tree.nodes.get("Principled BSDF")
        if shader:
            shader.inputs["Roughness"].default_value = 0.52
            shader.inputs["Specular IOR Level"].default_value = 0.22
            shader.inputs["Subsurface Weight"].default_value = 0.035
            shader.inputs["Subsurface Scale"].default_value = 0.00065

    for obj in [item for item in bpy.data.objects if item.type == "LIGHT"]:
        bpy.data.objects.remove(obj, do_unlink=True)
    scene = bpy.context.scene
    for name, location, energy, size, color in (
        ("V274G_KEY", (-0.65, -0.92, 2.06), 360.0, 0.80, (1.0, 0.90, 0.82)),
        ("V274G_FILL", (0.78, -0.68, 1.80), 150.0, 0.68, (0.72, 0.82, 1.0)),
        ("V274G_RIM", (0.42, 0.42, 1.98), 210.0, 0.60, (1.0, 0.76, 0.60)),
    ):
        data = bpy.data.lights.new(name + "_DATA", "AREA")
        data.energy, data.shape, data.size, data.color = energy, "DISK", size, color
        light = bpy.data.objects.new(name, data)
        scene.collection.objects.link(light)
        light.location = location
        point_at(light, Vector((0.0, -0.035, 1.64)))

    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1024
    scene.render.resolution_y = 1024
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.world.color = (0.016, 0.014, 0.013)
    camera = bpy.data.objects["V276E_CAMERA"]
    scene.camera = camera
    target = Vector((0.0, -0.03, 1.635))
    views = {
        "neutral_front": (Vector((0.0, -1.42, 1.64)), 92.0),
        "neutral_three_quarter": (Vector((-0.79, -1.12, 1.655)), 94.0),
        "neutral_profile": (Vector((-1.42, -0.01, 1.64)), 98.0),
    }
    keys = driver.data.shape_keys.key_blocks if driver.data.shape_keys else []
    for key in keys:
        if key.name not in {"Basis", "IDENTITY_LANDMARK_WARP"}:
            key.value = 0.0
    renders = {}
    for label, (location, lens) in views.items():
        camera.location = location
        camera.data.lens = lens
        point_at(camera, target)
        path = RENDERS / f"v274g_{label}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        renders[label] = {"path": str(path.relative_to(ROOT)), "sha256": sha(path)}

    expression = next((keys.get(name) for name in ("CTRL_Smile", "CTRL_Phoneme_E", "CTRL_Frown") if keys.get(name)), None)
    expression_record = None
    if expression:
        expression.value = 0.75
        bpy.context.view_layer.update()
        camera.location = Vector((0.0, -1.42, 1.64))
        camera.data.lens = 92.0
        point_at(camera, target)
        path = RENDERS / "v274g_expression_front.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        expression_record = {"shape": expression.name, "value": expression.value, "path": str(path.relative_to(ROOT)), "sha256": sha(path)}
        expression.value = 0.0
        bpy.context.view_layer.update()

    scene["V274G_STATUS"] = "FACEBUILDER_ANIMATION_BRIDGE_VISUAL_REVIEW_REQUIRED"
    scene["V274G_TRANSFERRED_SHAPES"] = len(shape_records)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v274g-facebuilder-animation-bridge-v1",
        "status": "BUILT_VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)},
        "donor": {"path": str(DONOR_BLEND.relative_to(ROOT)), "sha256": sha(DONOR_BLEND), "object": DONOR},
        "shape_transfer": {"target": driver.name, "mapping": mapping_record, "shapes": shape_records},
        "renders": renders,
        "expression": expression_record,
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha(OUTPUT)},
    }
    (AUDIT / "v274g_facebuilder_animation_bridge.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V274G_FACEBUILDER_BRIDGE_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
