"""Clean the V323 identity transfer against the locked character sheets."""

from pathlib import Path
import hashlib
import json

import bpy
from mathutils import Matrix, Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v323_identity_on_male" / "Character_An_identity_on_male_v323.blend"
STAGE = ROOT / "production_v324_identity_cleanup"
OUTPUT = STAGE / "Character_An_identity_cleanup_v324.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit" / "v324_identity_cleanup.json"
BODY = "V322_MB_MALE_BODY"
RIG = "V322_MB_MALE_RIG"
HEAD = "V216_REFERENCE_FITTED_HEAD"
GROOM = "V217_TIGHT_CURL_GROOM"
IDENTITY_NAMES = (
    HEAD,
    "V216_EYE_L", "V216_EYE_R",
    "V216_IRIS_L", "V216_IRIS_R",
    "V216_PUPIL_L", "V216_PUPIL_R",
    GROOM,
)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            digest.update(block)
    return digest.hexdigest()


def aim(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def bounds(obj):
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    lo = Vector(tuple(min(point[axis] for point in points) for axis in range(3)))
    hi = Vector(tuple(max(point[axis] for point in points) for axis in range(3)))
    return lo, hi


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


def remove_glasses():
    removed = []
    for obj in list(bpy.data.objects):
        if obj.name.startswith("V323_GLASSES"):
            removed.append(obj.name)
            bpy.data.objects.remove(obj, do_unlink=True)
    return removed


def replace_mask(obj, modifier_name, group_name, cutoff, keep_above):
    old_modifier = obj.modifiers.get(modifier_name)
    if old_modifier:
        obj.modifiers.remove(old_modifier)
    old_group = obj.vertex_groups.get(group_name)
    if old_group:
        obj.vertex_groups.remove(old_group)
    group = obj.vertex_groups.new(name=group_name)
    selected = []
    for vertex in obj.data.vertices:
        world_z = (obj.matrix_world @ vertex.co).z
        if world_z > cutoff:
            selected.append(vertex.index)
    group.add(selected, 1.0, "REPLACE")
    modifier = obj.modifiers.new(modifier_name, "MASK")
    modifier.vertex_group = group.name
    modifier.invert_vertex_group = not keep_above
    obj.modifiers.move(obj.modifiers.find(modifier.name), 0)
    return {
        "cutoff_z_m": cutoff,
        "selected_vertices": len(selected),
        "keep_above": keep_above,
        "modifier": modifier.name,
    }


def transform_world(obj, matrix):
    obj.matrix_world = matrix @ obj.matrix_world


def reshape_identity():
    head = bpy.data.objects[HEAD]
    head_lo, head_hi = bounds(head)
    pivot = Vector(((head_lo.x + head_hi.x) * 0.5, (head_lo.y + head_hi.y) * 0.5, head_hi.z))
    broadening = (
        Matrix.Translation(pivot)
        @ Matrix.Diagonal((1.08, 1.02, 1.0, 1.0))
        @ Matrix.Translation(-pivot)
    )
    for name in IDENTITY_NAMES:
        transform_world(bpy.data.objects[name], broadening)
    bpy.context.view_layer.update()

    groom = bpy.data.objects[GROOM]
    groom_lo, groom_hi = bounds(groom)
    groom_pivot = Vector(((groom_lo.x + groom_hi.x) * 0.5, (groom_lo.y + groom_hi.y) * 0.5, groom_lo.z))
    compact = (
        Matrix.Translation(groom_pivot)
        @ Matrix.Diagonal((0.92, 0.96, 0.72, 1.0))
        @ Matrix.Translation(-groom_pivot)
    )
    transform_world(groom, compact)
    bpy.context.view_layer.update()
    return {
        "identity_scale_xyz": [1.08, 1.02, 1.0],
        "groom_scale_xyz": [0.92, 0.96, 0.72],
    }


def tune_groom():
    groom = bpy.data.objects[GROOM]
    materials = []
    for slot in groom.material_slots:
        material = slot.material
        if material is None or material.node_tree is None:
            continue
        for node in material.node_tree.nodes:
            if node.type == "BSDF_HAIR_PRINCIPLED":
                values = {
                    "Color": (0.00035, 0.00045, 0.00065, 1.0),
                    "Melanin": 0.98,
                    "Melanin Redness": 0.01,
                    "Roughness": 0.38,
                    "Radial Roughness": 0.32,
                    "Random": 0.035,
                    "Random Color": 0.0,
                    "Tint": (0.025, 0.03, 0.04, 1.0),
                    "Absorption Coefficient": (2.4, 2.2, 2.0),
                }
                for name, value in values.items():
                    if name in node.inputs:
                        node.inputs[name].default_value = value
            elif node.type == "BSDF_PRINCIPLED":
                node.inputs["Base Color"].default_value = (0.0012, 0.0015, 0.0022, 1.0)
                node.inputs["Roughness"].default_value = 0.43
        materials.append(material.name)
    return materials


def grade_head_texture():
    head = bpy.data.objects[HEAD]
    touched = []
    for slot in head.material_slots:
        material = slot.material
        if material is None or material.node_tree is None:
            continue
        nodes = material.node_tree.nodes
        links = material.node_tree.links
        image = next((node for node in nodes if node.type == "TEX_IMAGE"), None)
        bsdf = next((node for node in nodes if node.type == "BSDF_PRINCIPLED"), None)
        if image is None or bsdf is None:
            continue
        for link in list(bsdf.inputs["Base Color"].links):
            links.remove(link)
        grade = nodes.get("V324_REFERENCE_SKIN_GRADE") or nodes.new("ShaderNodeMixRGB")
        grade.name = "V324_REFERENCE_SKIN_GRADE"
        grade.label = "Reference skin grade"
        grade.blend_type = "MULTIPLY"
        grade.inputs[0].default_value = 0.80
        grade.inputs[2].default_value = (0.625, 0.375, 0.19, 1.0)
        grade.location = (image.location.x + 220.0, image.location.y)
        links.new(image.outputs["Color"], grade.inputs[1])
        links.new(grade.outputs["Color"], bsdf.inputs["Base Color"])
        bsdf.inputs["Roughness"].default_value = 0.46
        bsdf.inputs["Specular IOR Level"].default_value = 0.34
        if "Subsurface Weight" in bsdf.inputs:
            bsdf.inputs["Subsurface Weight"].default_value = 0.075
        touched.append(material.name)
    return touched


def rebalance_lighting():
    energies = {"V323_KEY": 410.0, "V323_FILL": 145.0, "V323_RIM": 260.0}
    touched = {}
    for name, energy in energies.items():
        obj = bpy.data.objects.get(name)
        if obj and obj.type == "LIGHT":
            obj.data.energy = energy
            touched[name] = energy
    return touched


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    for folder in (STAGE, RENDERS, AUDIT.parent):
        folder.mkdir(parents=True, exist_ok=True)
    removed_glasses = remove_glasses()
    shape = reshape_identity()
    body = bpy.data.objects[BODY]
    head = bpy.data.objects[HEAD]
    old_body_modifier = body.modifiers.get("V323_HIDE_MB_HEAD")
    if old_body_modifier:
        body.modifiers.remove(old_body_modifier)
    old_body_group = body.vertex_groups.get("V323_HIDE_MB_HEAD")
    if old_body_group:
        body.vertex_groups.remove(old_body_group)
    body_mask = replace_mask(body, "V324_KEEP_BODY_BELOW_NECK", "V324_BODY_ABOVE_NECK", 1.592, False)
    head_mask = replace_mask(head, "V324_KEEP_IDENTITY_ABOVE_NECK", "V324_IDENTITY_ABOVE_NECK", 1.575, True)
    groom_materials = tune_groom()
    head_materials = grade_head_texture()
    lights = rebalance_lighting()
    bpy.context.view_layer.update()

    shape_count = len(head.data.shape_keys.key_blocks) - 1 if head.data.shape_keys else 0
    if shape_count != 51:
        raise RuntimeError(f"Expected 51 FACS shapes, found {shape_count}")
    scene = bpy.context.scene
    camera = bpy.data.objects["V323_CAMERA"]
    target = Vector((0.0, -0.055, 1.665))
    renders = {
        "portrait_front": render(scene, camera, RENDERS / "v324_portrait_front.png", Vector((0.0, -1.28, 1.67)), target, 104.0, (900, 900)),
        "portrait_three_quarter": render(scene, camera, RENDERS / "v324_portrait_three_quarter.png", Vector((0.58, -1.16, 1.70)), target, 100.0, (900, 900)),
        "portrait_profile": render(scene, camera, RENDERS / "v324_portrait_profile.png", Vector((1.22, -0.03, 1.67)), target, 100.0, (900, 900)),
        "full_front": render(scene, camera, RENDERS / "v324_full_front.png", Vector((0.0, -3.55, 1.02)), Vector((0.0, 0.0, 1.0)), 68.0, (900, 1100)),
    }
    scene["V324_STATUS"] = "IDENTITY_CLEANUP_VISUAL_REVIEW_REQUIRED"
    scene["V324_REFERENCE_LOCK"] = "NO_GLASSES_MEDIUM_BROWN_COMPACT_BLACK_CURLS"
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    head_lo, head_hi = bounds(head)
    groom_lo, groom_hi = bounds(bpy.data.objects[GROOM])
    record = {
        "schema": "v324-identity-cleanup-v1",
        "status": "BUILT_VISUAL_REVIEW_REQUIRED",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)},
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha(OUTPUT)},
        "reference_constraints": {
            "eyewear": "none",
            "skin": "medium-brown",
            "hair": "compact short black curls with side part",
        },
        "removed_glasses": removed_glasses,
        "shape": shape,
        "body_mask": body_mask,
        "head_mask": head_mask,
        "head_bounds_m": {"min": list(head_lo), "max": list(head_hi)},
        "groom_bounds_m": {"min": list(groom_lo), "max": list(groom_hi)},
        "facs_count": shape_count,
        "groom_materials": groom_materials,
        "head_materials": head_materials,
        "light_energies": lights,
        "renders": renders,
    }
    AUDIT.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V324_IDENTITY_CLEANUP_OK=" + json.dumps({
        "facs_count": shape_count,
        "head_bounds_m": [list(head_lo), list(head_hi)],
        "output_sha256": record["output"]["sha256"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
