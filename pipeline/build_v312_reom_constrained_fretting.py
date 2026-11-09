"""Replace the rejected looping IK solve with anatomically bounded FK contact."""

from pathlib import Path
import hashlib
import json

import bpy
import bmesh
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v310_reom_scene_alignment" / "Character_An_reom_scene_alignment_v310.blend"
STAGE = ROOT / "production_v312_reom_constrained_fretting"
OUTPUT = STAGE / "Character_An_reom_constrained_fretting_v312.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"
BODY = "V310_REOM_BODY"
RIG = "V310_REOM_RIG"
CONTACTS = {
    "index": {"target": Vector((0.2671270, -0.4045161, 1.3946022)), "string": "S5", "fret": 9},
    "middle": {"target": Vector((0.2444796, -0.4026991, 1.3896780)), "string": "S4", "fret": 10},
    "ring": {"target": Vector((0.2757289, -0.4060766, 1.3818460)), "string": "S7", "fret": 9},
    "pinky": {"target": Vector((0.2460079, -0.4042325, 1.3534319)), "string": "S8", "fret": 11},
}
THUMB_TARGET = Vector((0.2470, -0.3150, 1.3720))


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            digest.update(block)
    return digest.hexdigest()


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


def remove_charmorph_handlers():
    removed = []
    for handler in list(bpy.app.handlers.depsgraph_update_post):
        if getattr(handler, "__module__", "").startswith("CharMorph"):
            bpy.app.handlers.depsgraph_update_post.remove(handler)
            removed.append(f"{handler.__module__}.{handler.__name__}")
    return removed


def candidate_vertices(body, group_name, minimum_weight=0.10):
    group = body.vertex_groups.get(group_name)
    if group is None:
        raise RuntimeError(f"Missing vertex group {group_name}")
    indices = [
        vertex.index
        for vertex in body.data.vertices
        if any(item.group == group.index and item.weight >= minimum_weight for item in vertex.groups)
    ]
    if not indices:
        raise RuntimeError(f"No vertices weighted to {group_name}")
    return indices


def evaluated_positions(body):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = body.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    try:
        if len(mesh.vertices) != len(body.data.vertices):
            raise RuntimeError("Base-topology solve attempted with subdivision active")
        return [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    finally:
        evaluated.to_mesh_clear()


def solve_digit(rig, body, digit, target):
    prefix = f"f_{digit}" if digit != "thumb" else "thumb"
    ik_name = f"f_{digit}.01_ik.L" if digit != "thumb" else "thumb.01_ik.L"
    deform_name = f"DEF-f_{digit}.03.L" if digit != "thumb" else "DEF-thumb.03.L"
    rig.pose.bones[ik_name]["FK_IK"] = 0.0
    bones = [rig.pose.bones[f"{prefix}.{joint:02d}.L"] for joint in range(1, 4)]
    for bone in bones:
        bone.rotation_mode = "XYZ"
        bone.rotation_euler = (0.0, 0.0, 0.0)

    if digit == "thumb":
        parameters = [
            (bones[0], 0, -0.35, 1.30),
            (bones[0], 1, -0.65, 0.65),
            (bones[0], 2, -1.15, 1.15),
            (bones[1], 0, -0.25, 1.45),
            (bones[1], 2, -0.55, 0.55),
            (bones[2], 0, -0.20, 1.25),
        ]
        initial = (0.45, 0.0, -0.45, 0.55, -0.10, 0.35)
    else:
        parameters = [
            (bones[0], 0, 0.0, 1.30),
            (bones[0], 2, -0.80, 0.80),
            (bones[1], 0, 0.0, 1.55),
            (bones[2], 0, 0.0, 1.30),
        ]
        initial = (0.35, 0.0, 0.55, 0.40)
    for (bone, axis, _lower, _upper), value in zip(parameters, initial):
        bone.rotation_euler[axis] = value
    bpy.context.view_layer.update()

    candidates = candidate_vertices(body, deform_name)
    positions = evaluated_positions(body)
    pad_vertex = min(candidates, key=lambda index: (positions[index] - target).length_squared)

    def objective():
        point = evaluated_positions(body)[pad_vertex]
        contact = (point - target).length_squared
        regularizer = 1.0e-7 * sum(float(bone.rotation_euler[axis]) ** 2 for bone, axis, _lo, _hi in parameters)
        return contact + regularizer, point

    best, point = objective()
    evaluations = 1
    for step in (0.34, 0.18, 0.095, 0.050, 0.026, 0.013, 0.0065, 0.0032):
        for _pass in range(6):
            improved = False
            for bone, axis, lower, upper in parameters:
                base = float(bone.rotation_euler[axis])
                local_value, local_cost, local_point = base, best, point
                for candidate in (base - step, base + step):
                    if not lower <= candidate <= upper:
                        continue
                    bone.rotation_euler[axis] = candidate
                    bpy.context.view_layer.update()
                    cost, candidate_point = objective()
                    evaluations += 1
                    if cost < local_cost:
                        local_value, local_cost, local_point = candidate, cost, candidate_point
                bone.rotation_euler[axis] = local_value
                bpy.context.view_layer.update()
                if local_cost + 1.0e-14 < best:
                    best, point, improved = local_cost, local_point, True
            if not improved:
                break
    actual = evaluated_positions(body)[pad_vertex]
    return {
        "pad_vertex": pad_vertex,
        "candidate_vertex_count": len(candidates),
        "target_world_m": list(target),
        "actual_world_m": list(actual),
        "error_m": (actual - target).length,
        "evaluations": evaluations,
        "rotations_xyz_rad": {bone.name: list(bone.rotation_euler) for bone in bones},
        "limits": {
            f"{bone.name}:{'XYZ'[axis]}": [lower, upper]
            for bone, axis, lower, upper in parameters
        },
    }


def make_marker(name, location, material):
    mesh = bpy.data.meshes.new(f"{name}_MESH")
    builder = bmesh.new()
    bmesh.ops.create_icosphere(builder, subdivisions=2, radius=0.0038)
    builder.to_mesh(mesh)
    builder.free()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = location
    bpy.context.scene.collection.objects.link(obj)
    mesh.materials.append(material)
    return obj


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    removed_handlers = remove_charmorph_handlers()
    for folder in (STAGE, RENDERS, AUDIT):
        folder.mkdir(parents=True, exist_ok=True)
    body = bpy.data.objects[BODY]
    rig = bpy.data.objects[RIG]
    scene = bpy.context.scene
    scene.frame_set(1)
    subdivisions = [modifier for modifier in body.modifiers if modifier.type == "SUBSURF"]
    subdivision_states = [(modifier, modifier.show_viewport) for modifier in subdivisions]
    for modifier in subdivisions:
        modifier.show_viewport = False
    bpy.context.view_layer.update()

    solves = {}
    for digit, spec in CONTACTS.items():
        result = solve_digit(rig, body, digit, spec["target"])
        result.update({"string": spec["string"], "fret": spec["fret"], "depression_m": 0.00185})
        solves[digit] = result
    thumb = solve_digit(rig, body, "thumb", THUMB_TARGET)
    thumb["constraint"] = "rear-neck support; no top-edge crossing"

    for modifier, state in subdivision_states:
        modifier.show_viewport = state
    bpy.context.view_layer.update()

    marker_material = bpy.data.materials.new("V312_CONTACT_MARKER")
    marker_material.diffuse_color = (0.02, 0.72, 0.08, 1.0)
    markers = [make_marker(f"V312_TARGET_{digit.upper()}", spec["target"], marker_material) for digit, spec in CONTACTS.items()]
    markers.append(make_marker("V312_TARGET_THUMB", THUMB_TARGET, marker_material))

    camera = bpy.data.objects.get("V287_GUITAR_CAMERA")
    if camera is None:
        camera_data = bpy.data.cameras.new("V312_CAMERA")
        camera = bpy.data.objects.new("V312_CAMERA", camera_data)
        scene.collection.objects.link(camera)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.look = "AgX - Medium High Contrast"
    renders = {
        "diagnostic": render(
            scene, camera, RENDERS / "v312_diagnostic.png",
            Vector((0.72, -1.48, 1.49)), Vector((0.26, -0.39, 1.39)), 105.0, (1200, 900),
        ),
    }
    for obj in markers:
        obj.hide_render = True
        obj.hide_viewport = True
    renders.update({
        "front": render(
            scene, camera, RENDERS / "v312_front.png",
            Vector((0.72, -1.48, 1.49)), Vector((0.26, -0.39, 1.39)), 105.0, (1200, 900),
        ),
        "oblique": render(
            scene, camera, RENDERS / "v312_oblique.png",
            Vector((0.84, -1.02, 1.27)), Vector((0.26, -0.39, 1.39)), 98.0, (1200, 900),
        ),
        "rear": render(
            scene, camera, RENDERS / "v312_rear.png",
            Vector((0.38, 0.34, 1.43)), Vector((0.25, -0.36, 1.38)), 96.0, (1200, 900),
        ),
        "full": render(
            scene, camera, RENDERS / "v312_full.png",
            Vector((0.0, -3.75, 1.02)), Vector((0.0, -0.02, 1.0)), 66.0, (900, 1000),
        ),
    })

    max_error = max(result["error_m"] for result in solves.values())
    status = "CONSTRAINED_FK_VISUAL_REVIEW_REQUIRED"
    scene["V312_STATUS"] = status
    scene["V312_MAX_CONTACT_ERROR_M"] = max_error
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v312-reom-constrained-fretting-v1",
        "status": status,
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)},
        "rejected_predecessor": "V311 exact IK contact: looping/overlapping digits under visual review",
        "removed_session_handlers": removed_handlers,
        "protected_mapping": "index S5/F9; middle S4/F10; ring S7/F9; pinky S8/F11",
        "solves": solves,
        "thumb": thumb,
        "max_contact_error_m": max_error,
        "renders": renders,
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha(OUTPUT)},
    }
    (AUDIT / "v312_reom_constrained_fretting.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V312_REOM_CONSTRAINED_FRETTING_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
