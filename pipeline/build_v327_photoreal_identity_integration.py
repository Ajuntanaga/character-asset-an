"""Integrate the accepted V326 photoreal head onto the corrected male rig."""

from pathlib import Path
import hashlib
import json

import bpy
from mathutils import Matrix, Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
BODY_SOURCE = ROOT / "production_v324_identity_cleanup" / "Character_An_identity_cleanup_v324.blend"
HEAD_SOURCE = ROOT / "production_v326_photoreal_facebuilder" / "Character_An_photoreal_head_v326.blend"
STAGE = ROOT / "production_v327_photoreal_identity_integration"
OUTPUT = STAGE / "Character_An_photoreal_identity_v327.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit" / "v327_photoreal_identity.json"
BODY = "V322_MB_MALE_BODY"
RIG = "V322_MB_MALE_RIG"
HEAD = "V326_PHOTOREAL_FACEBUILDER_HEAD"
GROOM = "V217_TIGHT_CURL_GROOM"
OLD_IDENTITY = (
    "V216_REFERENCE_FITTED_HEAD",
    "V216_EYE_L", "V216_EYE_R",
    "V216_IRIS_L", "V216_IRIS_R",
    "V216_PUPIL_L", "V216_PUPIL_R",
)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            digest.update(block)
    return digest.hexdigest()


def bounds(obj):
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    lo = Vector(tuple(min(point[axis] for point in points) for axis in range(3)))
    hi = Vector(tuple(max(point[axis] for point in points) for axis in range(3)))
    return lo, hi


def aim(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


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


def remove_old_identity():
    removed = []
    for name in OLD_IDENTITY:
        obj = bpy.data.objects.get(name)
        if obj:
            removed.append(obj.name)
            bpy.data.objects.remove(obj, do_unlink=True)
    return removed


def append_head():
    with bpy.data.libraries.load(str(HEAD_SOURCE), link=False) as (source, target):
        if HEAD not in source.objects:
            raise RuntimeError(f"{HEAD} missing from {HEAD_SOURCE}")
        target.objects = [HEAD]
    head = target.objects[0]
    if head.name not in bpy.context.scene.collection.objects:
        bpy.context.scene.collection.objects.link(head)
    return head


def fit_head(head):
    source_lo, source_hi = bounds(head)
    source_center = (source_lo + source_hi) * 0.5
    target_width = 0.198
    scale = target_width / (source_hi.x - source_lo.x)
    target_center = Vector((0.0, -0.070, 1.800 - (source_hi.z - source_center.z) * scale))
    transform = Matrix.Translation(target_center) @ Matrix.Scale(scale, 4) @ Matrix.Translation(-source_center)
    head.matrix_world = transform @ head.matrix_world
    bpy.context.view_layer.update()
    return {
        "scale": scale,
        "target_width_m": target_width,
        "source_bounds": {"min": list(source_lo), "max": list(source_hi)},
    }


def replace_mask(obj, modifier_names, group_names, cutoff, keep_above):
    for name in modifier_names:
        modifier = obj.modifiers.get(name)
        if modifier:
            obj.modifiers.remove(modifier)
    for name in group_names:
        group = obj.vertex_groups.get(name)
        if group:
            obj.vertex_groups.remove(group)
    group_name = "V327_HEAD_ABOVE_NECK" if keep_above else "V327_BODY_ABOVE_NECK"
    group = obj.vertex_groups.new(name=group_name)
    selected = [
        vertex.index
        for vertex in obj.data.vertices
        if (obj.matrix_world @ vertex.co).z > cutoff
    ]
    group.add(selected, 1.0, "REPLACE")
    modifier = obj.modifiers.new("V327_KEEP_HEAD" if keep_above else "V327_KEEP_BODY", "MASK")
    modifier.vertex_group = group.name
    modifier.invert_vertex_group = not keep_above
    obj.modifiers.move(obj.modifiers.find(modifier.name), 0)
    return {"cutoff_z_m": cutoff, "selected_vertices": len(selected), "keep_above": keep_above}


def parent_to_head_bone(obj, rig):
    world = obj.matrix_world.copy()
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = "head"
    obj.matrix_world = world


def tune_head_material(head):
    materials = []
    for slot in head.material_slots:
        material = slot.material
        if not material or not material.node_tree:
            continue
        for node in material.node_tree.nodes:
            if node.type == "BSDF_PRINCIPLED":
                node.inputs["Roughness"].default_value = 0.43
                node.inputs["Specular IOR Level"].default_value = 0.32
                if "Subsurface Weight" in node.inputs:
                    node.inputs["Subsurface Weight"].default_value = 0.065
                if "Subsurface Scale" in node.inputs:
                    node.inputs["Subsurface Scale"].default_value = 0.007
        materials.append(material.name)
    return materials


def tune_body_material(body):
    skin = next((slot.material for slot in body.material_slots if slot.material and slot.material.name.startswith("charmorph_skin_v2")), None)
    if skin and skin.node_tree:
        nodes = skin.node_tree.nodes
        if "skin_color" in nodes:
            nodes["skin_color"].outputs[0].default_value = (0.080, 0.026, 0.014, 1.0)
        if "skin_roughness" in nodes:
            nodes["skin_roughness"].outputs[0].default_value = 0.46
        if "skin_sss_mix" in nodes:
            nodes["skin_sss_mix"].outputs[0].default_value = 0.14
    return skin.name if skin else None


def tune_groom(groom):
    groom_lo, groom_hi = bounds(groom)
    pivot = Vector(((groom_lo.x + groom_hi.x) * 0.5, (groom_lo.y + groom_hi.y) * 0.5, groom_lo.z))
    compact = Matrix.Translation(pivot) @ Matrix.Diagonal((0.94, 0.96, 0.76, 1.0)) @ Matrix.Translation(-pivot)
    groom.matrix_world = compact @ groom.matrix_world
    for slot in groom.material_slots:
        material = slot.material
        if not material or not material.node_tree:
            continue
        for node in material.node_tree.nodes:
            if node.type == "BSDF_HAIR_PRINCIPLED":
                if "Color" in node.inputs:
                    node.inputs["Color"].default_value = (0.00003, 0.00004, 0.00006, 1.0)
                if "Melanin" in node.inputs:
                    node.inputs["Melanin"].default_value = 1.0
                if "Melanin Redness" in node.inputs:
                    node.inputs["Melanin Redness"].default_value = 0.0
                if "Absorption Coefficient" in node.inputs:
                    node.inputs["Absorption Coefficient"].default_value = (12.0, 12.0, 12.0)
            elif node.type == "BSDF_PRINCIPLED":
                node.inputs["Base Color"].default_value = (0.0002, 0.00025, 0.00035, 1.0)
    return {"scale_xyz": [0.94, 0.96, 0.76]}


def tune_lights():
    settings = {
        "V323_KEY": (430.0, (1.0, 0.97, 0.94)),
        "V323_FILL": (185.0, (0.82, 0.90, 1.0)),
        "V323_RIM": (135.0, (0.68, 0.76, 1.0)),
    }
    for name, (energy, color) in settings.items():
        light = bpy.data.objects.get(name)
        if light and light.type == "LIGHT":
            light.data.energy = energy
            light.data.color = color
    return settings


def main():
    bpy.ops.wm.open_mainfile(filepath=str(BODY_SOURCE))
    for folder in (STAGE, RENDERS, AUDIT.parent):
        folder.mkdir(parents=True, exist_ok=True)
    removed = remove_old_identity()
    head = append_head()
    fit = fit_head(head)
    body = bpy.data.objects[BODY]
    rig = bpy.data.objects[RIG]
    body_mask = replace_mask(
        body,
        ("V323_HIDE_MB_HEAD", "V324_KEEP_BODY_BELOW_NECK"),
        ("V323_HIDE_MB_HEAD", "V324_BODY_ABOVE_NECK"),
        1.592,
        False,
    )
    head_mask = replace_mask(head, (), (), 1.574, True)
    parent_to_head_bone(head, rig)
    head_materials = tune_head_material(head)
    body_material = tune_body_material(body)
    groom = bpy.data.objects.get(GROOM)
    groom_stats = tune_groom(groom) if groom else None
    lights = tune_lights()
    bpy.context.view_layer.update()

    shape_count = len(head.data.shape_keys.key_blocks) - 1 if head.data.shape_keys else 0
    if shape_count != 51:
        raise RuntimeError(f"Expected 51 FACS shapes, found {shape_count}")
    scene = bpy.context.scene
    scene["V327_STATUS"] = "PHOTOREAL_IDENTITY_INTEGRATED_VISUAL_REVIEW_REQUIRED"
    scene["V327_FACS_COUNT"] = shape_count
    camera = bpy.data.objects["V323_CAMERA"]
    target = Vector((0.0, -0.065, 1.665))
    renders = {
        "portrait_front": render(scene, camera, RENDERS / "v327_portrait_front.png", Vector((0.0, -1.28, 1.67)), target, 104.0, (900, 900)),
        "portrait_three_quarter": render(scene, camera, RENDERS / "v327_portrait_three_quarter.png", Vector((0.58, -1.16, 1.70)), target, 100.0, (900, 900)),
        "portrait_profile": render(scene, camera, RENDERS / "v327_portrait_profile.png", Vector((1.22, -0.03, 1.67)), target, 100.0, (900, 900)),
        "full_front": render(scene, camera, RENDERS / "v327_full_front.png", Vector((0.0, -3.55, 1.02)), Vector((0.0, 0.0, 1.0)), 68.0, (900, 1100)),
    }
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    lo, hi = bounds(head)
    record = {
        "schema": "v327-photoreal-identity-integration-v1",
        "status": "BUILT_VISUAL_REVIEW_REQUIRED",
        "body_source": {"path": str(BODY_SOURCE.relative_to(ROOT)), "sha256": sha(BODY_SOURCE)},
        "head_source": {"path": str(HEAD_SOURCE.relative_to(ROOT)), "sha256": sha(HEAD_SOURCE)},
        "removed_old_identity": removed,
        "fit": fit,
        "head_bounds_m": {"min": list(lo), "max": list(hi)},
        "body_mask": body_mask,
        "head_mask": head_mask,
        "facs_count": shape_count,
        "head_materials": head_materials,
        "body_material": body_material,
        "groom": groom_stats,
        "lights": lights,
        "renders": renders,
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha(OUTPUT)},
    }
    AUDIT.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V327_PHOTOREAL_IDENTITY_OK=" + json.dumps({
        "facs_count": shape_count,
        "head_bounds_m": [list(lo), list(hi)],
        "output_sha256": record["output"]["sha256"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
