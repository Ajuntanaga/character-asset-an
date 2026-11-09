"""Solve the Reom finger IK controls onto the protected V237 contact map."""

from pathlib import Path
import hashlib
import json

import bpy
import bmesh
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v310_reom_scene_alignment" / "Character_An_reom_scene_alignment_v310.blend"
STAGE = ROOT / "production_v311_reom_fretting_contact"
OUTPUT = STAGE / "Character_An_reom_fretting_contact_v311.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit"
BODY = "V310_REOM_BODY"
RIG = "V310_REOM_RIG"

# V237/V253 protected contact authority: pad centers are 18 percent behind
# the fret wire and include 1.85 mm of local string depression.
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


def candidate_vertices(body, group_name, minimum_weight=0.10):
    group = body.vertex_groups.get(group_name)
    if group is None:
        raise RuntimeError(f"Missing vertex group {group_name}")
    result = []
    for vertex in body.data.vertices:
        if any(item.group == group.index and item.weight >= minimum_weight for item in vertex.groups):
            result.append(vertex.index)
    if not result:
        raise RuntimeError(f"No vertices weighted to {group_name}")
    return result


def evaluated_base_positions(body):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = body.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    try:
        if len(mesh.vertices) != len(body.data.vertices):
            raise RuntimeError(
                f"Solver requires base topology; evaluated {len(mesh.vertices)} != source {len(body.data.vertices)}"
            )
        return [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    finally:
        evaluated.to_mesh_clear()


def solve_pad_contact(rig, body, digit, target, tolerance=0.00035, iterations=16):
    control_name = f"f_{digit}.01_ik.L" if digit != "thumb" else "thumb.01_ik.L"
    deform_name = f"DEF-f_{digit}.03.L" if digit != "thumb" else "DEF-thumb.03.L"
    control = rig.pose.bones[control_name]
    control["FK_IK"] = 1.0
    world = rig.matrix_world @ control.matrix
    world.translation = target.copy()
    control.matrix = rig.matrix_world.inverted() @ world
    bpy.context.view_layer.update()

    candidates = candidate_vertices(body, deform_name)
    positions = evaluated_base_positions(body)
    pad_vertex = min(candidates, key=lambda index: (positions[index] - target).length_squared)
    trace = []
    for iteration in range(iterations):
        positions = evaluated_base_positions(body)
        actual = positions[pad_vertex]
        delta = target - actual
        error = delta.length
        trace.append(error)
        if error <= tolerance:
            break
        world = rig.matrix_world @ control.matrix
        world.translation += delta * 0.88
        control.matrix = rig.matrix_world.inverted() @ world
        bpy.context.view_layer.update()

    positions = evaluated_base_positions(body)
    actual = positions[pad_vertex]
    chain = [
        rig.pose.bones[f"DEF-f_{digit}.{joint:02d}.L"] if digit != "thumb"
        else rig.pose.bones[f"DEF-thumb.{joint:02d}.L"]
        for joint in range(1, 4)
    ]
    segment_lengths = [(bone.tail - bone.head).length for bone in chain]
    return {
        "control": control_name,
        "deform_group": deform_name,
        "candidate_vertex_count": len(candidates),
        "pad_vertex": pad_vertex,
        "target_world_m": list(target),
        "actual_world_m": list(actual),
        "error_m": (actual - target).length,
        "iterations": len(trace),
        "error_trace_m": trace,
        "segment_lengths_m": segment_lengths,
        "control_world_translation_m": list((rig.matrix_world @ control.matrix).translation),
    }


def marker(name, location, material):
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
        result = solve_pad_contact(rig, body, digit, spec["target"])
        result.update({
            "string": spec["string"],
            "fret": spec["fret"],
            "depression_m": 0.00185,
            "pad_fraction_behind_fret": 0.18,
        })
        solves[digit] = result
    thumb = solve_pad_contact(rig, body, "thumb", THUMB_TARGET, tolerance=0.00055)
    thumb["constraint"] = "rear-neck support; must not cross top edge"

    for modifier, state in subdivision_states:
        modifier.show_viewport = state
    bpy.context.view_layer.update()

    marker_material = bpy.data.materials.new("V311_CONTACT_MARKER")
    marker_material.diffuse_color = (0.03, 0.80, 0.10, 1.0)
    marker_material.use_nodes = True
    marker_bsdf = marker_material.node_tree.nodes.get("Principled BSDF")
    marker_bsdf.inputs["Base Color"].default_value = (0.01, 0.65, 0.03, 1.0)
    marker_bsdf.inputs["Emission Color"].default_value = (0.01, 0.45, 0.02, 1.0)
    marker_bsdf.inputs["Emission Strength"].default_value = 2.2
    markers = [marker(f"V311_CONTACT_{digit.upper()}", spec["target"], marker_material) for digit, spec in CONTACTS.items()]
    markers.append(marker("V311_CONTACT_THUMB", THUMB_TARGET, marker_material))

    camera = bpy.data.objects.get("V287_GUITAR_CAMERA")
    if camera is None:
        camera_data = bpy.data.cameras.new("V311_CONTACT_CAMERA")
        camera = bpy.data.objects.new("V311_CONTACT_CAMERA", camera_data)
        scene.collection.objects.link(camera)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.look = "AgX - Medium High Contrast"
    renders = {
        "contact_diagnostic": render(
            scene, camera, RENDERS / "v311_contact_diagnostic.png",
            Vector((0.72, -1.48, 1.49)), Vector((0.26, -0.39, 1.39)), 105.0, (1200, 900),
        ),
    }
    for obj in markers:
        obj.hide_render = True
        obj.hide_viewport = True
    renders.update({
        "contact_front": render(
            scene, camera, RENDERS / "v311_contact_front.png",
            Vector((0.72, -1.48, 1.49)), Vector((0.26, -0.39, 1.39)), 105.0, (1200, 900),
        ),
        "contact_oblique": render(
            scene, camera, RENDERS / "v311_contact_oblique.png",
            Vector((0.84, -1.02, 1.27)), Vector((0.26, -0.39, 1.39)), 98.0, (1200, 900),
        ),
        "contact_rear": render(
            scene, camera, RENDERS / "v311_contact_rear.png",
            Vector((0.38, 0.34, 1.43)), Vector((0.25, -0.36, 1.38)), 96.0, (1200, 900),
        ),
        "full": render(
            scene, camera, RENDERS / "v311_full.png",
            Vector((0.0, -3.75, 1.02)), Vector((0.0, -0.02, 1.0)), 66.0, (900, 1000),
        ),
    })

    max_contact_error = max(result["error_m"] for result in solves.values())
    status = "CONTACT_SOLVED_VISUAL_REVIEW_REQUIRED" if max_contact_error <= 0.0015 else "CONTACT_NUMERIC_REFINEMENT_REQUIRED"
    scene["V311_STATUS"] = status
    scene["V311_MAX_CONTACT_ERROR_M"] = max_contact_error
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    record = {
        "schema": "v311-reom-fretting-contact-v1",
        "status": status,
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)},
        "protected_mapping": "index S5/F9; middle S4/F10; ring S7/F9; pinky S8/F11",
        "solves": solves,
        "thumb": thumb,
        "max_contact_error_m": max_contact_error,
        "renders": renders,
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": sha(OUTPUT)},
    }
    (AUDIT / "v311_reom_fretting_contact.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V311_REOM_FRETTING_CONTACT_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
