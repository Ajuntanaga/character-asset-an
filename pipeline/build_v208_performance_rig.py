from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.build_v207_playable_hands import capsule, collection, curve_detail, ellipsoid, material, move_to_collection
from pipeline.common import sha256, write_json


STAGE = ROOT / "production_v208_rig"
SOURCE = ROOT / "production_v207_hands" / "ant_playable_hands_v207.blend"
OUTPUT = STAGE / "ant_performance_rig_v208.blend"
EXPECTED_SOURCE_SHA256 = "6c5b144ceeec8b7b5b7e4a89bde4e1be53bed09465eabc2c42d7a772cf5c22f5"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def trimmed_copy(source: bpy.types.Object, name: str, predicate, target: bpy.types.Collection) -> bpy.types.Object:
    selected = []
    used: set[int] = set()
    for polygon in source.data.polygons:
        world = source.matrix_world @ polygon.center
        if predicate(world):
            selected.append(polygon)
            used.update(polygon.vertices)
    mapping = {old: new for new, old in enumerate(sorted(used))}
    vertices = [tuple(source.data.vertices[index].co) for index in sorted(used)]
    faces = [tuple(mapping[index] for index in polygon.vertices) for polygon in selected]
    mesh = bpy.data.meshes.new(name + "_MESH")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    target.objects.link(obj)
    obj.matrix_world = source.matrix_world.copy()
    for mat in source.data.materials:
        obj.data.materials.append(mat)
    for polygon, source_polygon in zip(obj.data.polygons, selected):
        polygon.use_smooth = True
        polygon.material_index = source_polygon.material_index
    obj["trimmed_from"] = source.name
    obj["face_count"] = len(faces)
    return obj


def create_armature(target: bpy.types.Collection, points: dict[str, tuple[Vector, Vector, str | None]]) -> bpy.types.Object:
    old = bpy.data.objects.get("V208_PERFORMANCE_RIG")
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    data = bpy.data.armatures.new("V208_PERFORMANCE_RIG_DATA")
    rig = bpy.data.objects.new("V208_PERFORMANCE_RIG", data)
    target.objects.link(rig)
    rig.show_in_front = True
    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bones = {}
    for name, (head, tail, parent_name) in points.items():
        bone = data.edit_bones.new(name)
        bone.head = head
        bone.tail = tail
        bones[name] = bone
        if parent_name:
            bone.parent = bones[parent_name]
    bpy.ops.object.mode_set(mode="POSE")
    for pose_bone in rig.pose.bones:
        pose_bone.rotation_mode = "XYZ"
        pose_bone["v208_control"] = True
    bpy.ops.object.mode_set(mode="OBJECT")
    rig["checkpoint"] = "V208_PERFORMANCE_RIG"
    rig["rig_type"] = "FK performance control rig with explicit hand and guitar controls"
    return rig


def create_sleeve(name: str, points: list[Vector], radius: float, mat: bpy.types.Material, target: bpy.types.Collection) -> list[bpy.types.Object]:
    created = []
    for index in range(len(points) - 1):
        segment_radius = radius * (1.0 - index * 0.08)
        created.extend(capsule(f"V208_{name}_SLEEVE_{index + 1}", points[index], points[index + 1], segment_radius, mat, target, 0.96))
    cuff = ellipsoid(f"V208_{name}_CUFF", points[-1], (radius * 0.90, radius * 0.92, radius * 0.78), mat, target, points[-1] - points[-2])
    created.append(cuff)
    return created


def strap_segment(name: str, start: Vector, end: Vector, mat: bpy.types.Material, target: bpy.types.Collection) -> bpy.types.Object:
    vector = end - start
    bpy.ops.mesh.primitive_cube_add(location=(start + end) * 0.5)
    obj = bpy.context.object
    obj.name = name
    obj.scale = (0.020, 0.0030, vector.length * 0.5)
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = Vector((0.0, 0.0, 1.0)).rotation_difference(vector.normalized())
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    move_to_collection(obj, target)
    obj.data.materials.append(mat)
    bevel = obj.modifiers.new("Leather edge roll", "BEVEL")
    bevel.width = 0.0025
    bevel.segments = 3
    return obj


def create_picking_hand(target: bpy.types.Collection, skin: bpy.types.Material, nail: bpy.types.Material) -> dict[str, object]:
    palm_center = Vector((0.055, -0.245, 1.000))
    palm = ellipsoid("V208_PICKING_PALM", palm_center, (0.031, 0.018, 0.040), skin, target, Vector((-0.55, -0.20, 0.81)))
    wrist = Vector((0.085, -0.220, 1.045))
    thumb = [Vector((0.047, -0.258, 1.018)), Vector((0.020, -0.270, 0.998)), Vector((0.006, -0.276, 0.980))]
    index = [Vector((0.048, -0.260, 0.990)), Vector((0.025, -0.278, 0.970)), Vector((0.005, -0.282, 0.975))]
    created = [palm]
    for digit, points, radius in (("THUMB", thumb, 0.0065), ("INDEX", index, 0.0058)):
        for number in range(len(points) - 1):
            created.extend(capsule(f"V208_PICKING_{digit}_{number + 1}", points[number], points[number + 1], radius * (1.0 - number * 0.10), skin, target))
    for digit, offset in (("MIDDLE", Vector((0.010, 0.001, -0.010))), ("RING", Vector((0.017, 0.004, -0.018))), ("PINKY", Vector((0.024, 0.008, -0.024)))):
        start = Vector((0.058, -0.250, 0.988)) + offset
        mid = Vector((0.042, -0.265, 0.966)) + offset
        end = Vector((0.035, -0.258, 0.949)) + offset
        created.extend(capsule(f"V208_PICKING_{digit}_1", start, mid, 0.0055, skin, target))
        created.extend(capsule(f"V208_PICKING_{digit}_2", mid, end, 0.0050, skin, target))
    mesh = bpy.data.meshes.new("V208_PICK_MESH")
    mesh.from_pydata([(-0.010, 0.0, 0.006), (0.011, 0.0, 0.0), (-0.010, 0.0, -0.006)], [], [(0, 1, 2)])
    pick = bpy.data.objects.new("V208_PICK", mesh)
    target.objects.link(pick)
    pick.location = (0.004, -0.285, 0.979)
    pick.rotation_euler = (math.radians(82), math.radians(8), math.radians(-22))
    pick.data.materials.append(material("MAT_V208_PICK", (0.008, 0.010, 0.012, 1.0), 0.35))
    pick["pinched_by"] = "thumb_index"
    created.append(pick)
    return {"objects": created, "palm": palm, "wrist": wrist, "pick": pick}


def guitar_performance_matrix() -> Matrix:
    local_x = Vector((0.819152, 0.0, -0.573576))
    local_y = Vector((0.573576, 0.0, 0.819152))
    local_z = Vector((0.0, -1.0, 0.0))
    location = Vector((-0.570, -0.180, 1.350))
    return Matrix((
        (local_x.x, local_y.x, local_z.x, location.x),
        (local_x.y, local_y.y, local_z.y, location.y),
        (local_x.z, local_y.z, local_z.z, location.z),
        (0.0, 0.0, 0.0, 1.0),
    ))


def add_camera(name: str, location: tuple[float, float, float], look: tuple[float, float, float], lens: float, target: bpy.types.Collection) -> bpy.types.Object:
    data = bpy.data.cameras.new(name + "_DATA")
    data.lens = lens
    obj = bpy.data.objects.new(name, data)
    target.objects.link(obj)
    obj.location = location
    obj.rotation_euler = (Vector(look) - obj.location).to_track_quat("-Z", "Y").to_euler()
    return obj


def add_light(name: str, location: tuple[float, float, float], look: tuple[float, float, float], energy: float, size: float, target: bpy.types.Collection) -> bpy.types.Object:
    data = bpy.data.lights.new(name + "_DATA", "AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size
    obj = bpy.data.objects.new(name, data)
    target.objects.link(obj)
    obj.location = location
    obj.rotation_euler = (Vector(look) - obj.location).to_track_quat("-Z", "Y").to_euler()
    return obj


def build() -> dict[str, object]:
    target = collection("V208_PERFORMANCE")
    for obj in tuple(target.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    guitar_root = bpy.data.objects["V206_GUITAR_ROOT"]
    guitar_root.matrix_world = guitar_performance_matrix()
    guitar_root["v208_performance_placement"] = True

    body = bpy.data.objects["V202_BODY"]
    jacket = bpy.data.objects["V205_FITTED_JACKET_SHELL"]
    body_trim = trimmed_copy(body, "V208_BODY_WITHOUT_NEUTRAL_ARMS", lambda p: not (0.78 < p.z < 1.56 and abs(p.x) > 0.175), target)
    jacket_trim = trimmed_copy(jacket, "V208_JACKET_TORSO", lambda p: abs(p.x) < 0.225 or p.z > 1.49, target)
    body.hide_render = True
    jacket.hide_render = True
    for obj in bpy.data.objects:
        if obj.name.startswith("V202_NAIL_HAND_"):
            obj.hide_render = True

    jacket_mat = bpy.data.materials["MAT_V205_CHARCOAL_JACKET"]
    skin = bpy.data.materials.get("MAT_V207_SKIN") or bpy.data.materials["MAT_V203_SKIN"]
    nail = bpy.data.materials.get("MAT_V207_NAIL") or bpy.data.materials["MAT_V203_NAIL"]
    # The trimmed mesh has no inherited UV layer. Use the procedural skin
    # material rather than the UV-dependent V203 surface, which renders magenta.
    body_trim.data.materials.clear()
    body_trim.data.materials.append(skin)
    fretting_points = [Vector((-0.205, -0.020, 1.475)), Vector((-0.355, -0.125, 1.335)), Vector((-0.205, -0.205, 1.105))]
    picking_points = [Vector((0.205, -0.020, 1.475)), Vector((0.330, -0.125, 1.260)), Vector((0.085, -0.220, 1.045))]
    sleeves = create_sleeve("FRETTING", fretting_points, 0.058, jacket_mat, target)
    sleeves += create_sleeve("PICKING", picking_points, 0.058, jacket_mat, target)
    picking = create_picking_hand(target, skin, nail)

    bones = {
        "root": (Vector((0, 0, 0)), Vector((0, 0, 0.18)), None),
        "pelvis": (Vector((0, 0, 0.82)), Vector((0, 0, 0.98)), "root"),
        "spine_01": (Vector((0, 0, 0.98)), Vector((0, 0, 1.22)), "pelvis"),
        "spine_02": (Vector((0, 0, 1.22)), Vector((0, 0, 1.46)), "spine_01"),
        "neck": (Vector((0, 0, 1.46)), Vector((0, 0, 1.58)), "spine_02"),
        "head": (Vector((0, 0, 1.58)), Vector((0, 0, 1.76)), "neck"),
        "clavicle_fretting": (Vector((0, 0, 1.46)), fretting_points[0], "spine_02"),
        "upper_arm_fretting": (fretting_points[0], fretting_points[1], "clavicle_fretting"),
        "forearm_fretting": (fretting_points[1], fretting_points[2], "upper_arm_fretting"),
        "hand_fretting": (fretting_points[2], fretting_points[2] + Vector((-0.06, -0.02, 0.04)), "forearm_fretting"),
        "clavicle_picking": (Vector((0, 0, 1.46)), picking_points[0], "spine_02"),
        "upper_arm_picking": (picking_points[0], picking_points[1], "clavicle_picking"),
        "forearm_picking": (picking_points[1], picking_points[2], "upper_arm_picking"),
        "hand_picking": (picking_points[2], picking_points[2] + Vector((-0.05, -0.03, -0.03)), "forearm_picking"),
        "guitar_ctrl": (Vector((-0.05, -0.18, 0.95)), Vector((-0.05, -0.18, 1.15)), "spine_01"),
        "pick_ctrl": (Vector((0.004, -0.285, 0.979)), Vector((0.004, -0.285, 1.029)), "hand_picking"),
    }
    rig = create_armature(target, bones)
    for obj in sleeves:
        obj["rig_controlled"] = True
    picking["palm"]["rig_controlled"] = True

    strap_mat = material("MAT_V208_STRAP", (0.006, 0.007, 0.008, 1.0), 0.62)
    strap_points = [Vector((-0.16, -0.10, 1.48)), Vector((0.16, -0.14, 1.28)), Vector((0.24, -0.16, 0.96))]
    strap_parts = [strap_segment(f"V208_GUITAR_STRAP_{index + 1}", strap_points[index], strap_points[index + 1], strap_mat, target) for index in range(2)]
    for strap in strap_parts:
        strap["role"] = "weight-bearing guitar strap"
    return {"rig": rig, "body_trim": body_trim, "jacket_trim": jacket_trim, "sleeves": sleeves, "picking": picking, "strap": strap_parts}


def render_suite(cameras: dict[str, bpy.types.Object]) -> dict[str, object]:
    scene = bpy.context.scene
    render_dir = STAGE / "renders" / "performance"
    render_dir.mkdir(parents=True, exist_ok=True)
    visibility = {obj.name: obj.hide_render for obj in bpy.data.objects}
    for obj in bpy.data.objects:
        if obj.type == "LIGHT":
            obj.hide_render = not obj.name.startswith("V208_")
        if obj.name.startswith(("V208_CAM_", "V207_CAM_", "V206_CAM_")):
            obj.hide_render = True
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 32
    scene.cycles.use_denoising = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.resolution_percentage = 100
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.view_settings.exposure = -1.55
    scene.world.use_nodes = True
    background = scene.world.node_tree.nodes.get("Background")
    if background:
        background.inputs["Color"].default_value = (0.006, 0.008, 0.012, 1.0)
        background.inputs["Strength"].default_value = 0.10
    manifest = {"renderer": "Cycles CPU", "renders": {}}
    try:
        for label, camera in cameras.items():
            scene.camera = camera
            if label in {"front", "three_quarter", "profile", "hero"}:
                scene.render.resolution_x, scene.render.resolution_y = 720, 960
            else:
                scene.render.resolution_x, scene.render.resolution_y = 800, 680
            output = render_dir / f"{label}.png"
            scene.render.filepath = str(output)
            bpy.ops.render.render(write_still=True)
            manifest["renders"][label] = {"path": str(output.relative_to(ROOT)), "sha256": sha256(output)}
    finally:
        for name, hidden in visibility.items():
            obj = bpy.data.objects.get(name)
            if obj:
                obj.hide_render = hidden
    write_json(STAGE / "audit" / "v208_render_manifest.json", manifest)
    return manifest


def main() -> None:
    require(Path(bpy.data.filepath).resolve() == SOURCE.resolve(), f"Open accepted V207 source first: {SOURCE}")
    require(sha256(SOURCE) == EXPECTED_SOURCE_SHA256, "Accepted V207 source hash changed")
    STAGE.joinpath("audit").mkdir(parents=True, exist_ok=True)
    result = build()
    target = collection("V208_PERFORMANCE")
    cameras = {
        "front": add_camera("V208_CAM_FRONT", (0.0, -4.0, 0.95), (0.0, 0.0, 0.92), 72, target),
        "three_quarter": add_camera("V208_CAM_THREE_QUARTER", (2.7, -3.2, 1.15), (0.0, -0.02, 0.98), 78, target),
        "profile": add_camera("V208_CAM_PROFILE", (-3.4, -0.25, 1.05), (0.0, -0.02, 1.0), 82, target),
        "fretting_contact": add_camera("V208_CAM_FRETTING", (-0.48, -1.05, 1.48), (-0.28, -0.19, 1.20), 105, target),
        "picking_contact": add_camera("V208_CAM_PICKING", (0.50, -1.05, 1.22), (0.04, -0.22, 1.00), 105, target),
        "hero": add_camera("V208_CAM_HERO", (2.2, -3.8, 1.35), (0.0, -0.04, 1.00), 88, target),
    }
    add_light("V208_KEY", (1.1, -2.0, 3.2), (0.0, 0.0, 1.0), 620.0, 1.2, target)
    add_light("V208_FILL", (-1.8, -1.0, 2.1), (0.0, 0.0, 1.0), 180.0, 1.0, target)
    add_light("V208_RIM", (0.3, 1.7, 2.8), (0.0, 0.0, 1.2), 420.0, 0.9, target)
    scene = bpy.context.scene
    scene["checkpoint"] = "V208_PERFORMANCE_RIG"
    scene["source_v207_sha256"] = EXPECTED_SOURCE_SHA256
    scene["v208_rig_bones"] = len(result["rig"].data.bones)
    scene["v208_pose"] = "standing eight-string performance pose with fretting and picking contacts"
    audit = {
        "schema": "v208-performance-rig-v1",
        "status": "PASS",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": EXPECTED_SOURCE_SHA256},
        "rig": {"object": result["rig"].name, "bones": sorted(bone.name for bone in result["rig"].data.bones)},
        "performance": {"guitar_matrix": [list(row) for row in bpy.data.objects["V206_GUITAR_ROOT"].matrix_world], "pick": "thumb-index pinch", "strap": [obj.name for obj in result["strap"]]},
        "replacement_surfaces": {"body": result["body_trim"].name, "jacket": result["jacket_trim"].name},
    }
    write_json(STAGE / "audit" / "v208_rig_audit.json", audit)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    render_suite(cameras)
    output_hash = sha256(OUTPUT)
    write_json(STAGE / "audit" / "v208_build_receipt.json", {
        "status": "PASS",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": EXPECTED_SOURCE_SHA256},
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": output_hash},
        "rig_audit_sha256": sha256(STAGE / "audit" / "v208_rig_audit.json"),
        "render_manifest_sha256": sha256(STAGE / "audit" / "v208_render_manifest.json"),
    })
    print(f"V208_PERFORMANCE_RIG_OK output_sha256={output_hash} bones={len(result['rig'].data.bones)}")


if __name__ == "__main__":
    main()
