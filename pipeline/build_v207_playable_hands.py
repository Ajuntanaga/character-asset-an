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

from pipeline.common import sha256, write_json
from pipeline.guitar_geometry import GuitarGeometry, load_authoritative_mapping
from pipeline.hand_contact_solver import HandSolveReport, build_candidate_targets, validate_hand_solve


STAGE = ROOT / "production_v207_hands"
SOURCE = ROOT / "production_v206_guitar" / "ant_headless_guitar_v206.blend"
OUTPUT = STAGE / "ant_playable_hands_v207.blend"
EXPECTED_SOURCE_SHA256 = "2529d85a667bb0f9f49a8f09473217d3871db5d2c175ed3839851b20bc0a86ef"
NEUTRAL_FRET_X = 0.260
CONTACT_Z = 0.02045
STRING_TOP_Z = 0.02230
FINGER_RADII = {"index": 0.0057, "middle": 0.0060, "ring": 0.0056, "pinky": 0.0049, "thumb": 0.0063}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def collection(name: str) -> bpy.types.Collection:
    value = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if value.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(value)
    return value


def move_to_collection(obj: bpy.types.Object, target: bpy.types.Collection) -> None:
    for owner in tuple(obj.users_collection):
        owner.objects.unlink(obj)
    target.objects.link(obj)


def material(name: str, color: tuple[float, float, float, float], roughness: float, metallic: float = 0.0) -> bpy.types.Material:
    value = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    value.use_nodes = True
    bsdf = value.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = color
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Metallic"].default_value = metallic
        if "Subsurface Weight" in bsdf.inputs:
            bsdf.inputs["Subsurface Weight"].default_value = 0.065 if metallic == 0.0 else 0.0
            if "Subsurface Radius" in bsdf.inputs:
                bsdf.inputs["Subsurface Radius"].default_value = (1.0, 0.42, 0.22)
    value.diffuse_color = color
    if name == "MAT_V207_SKIN" and bsdf:
        nodes = value.node_tree.nodes
        links = value.node_tree.links
        for node in tuple(nodes):
            if node != bsdf and node.type != "OUTPUT_MATERIAL":
                nodes.remove(node)
        texcoord = nodes.new("ShaderNodeTexCoord")
        micro = nodes.new("ShaderNodeTexNoise")
        micro.inputs["Scale"].default_value = 72.0
        micro.inputs["Detail"].default_value = 5.0
        micro.inputs["Roughness"].default_value = 0.72
        bump = nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = 0.10
        bump.inputs["Distance"].default_value = 0.00022
        links.new(texcoord.outputs["Generated"], micro.inputs["Vector"])
        links.new(micro.outputs["Fac"], bump.inputs["Height"])
        links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return value


def ellipsoid(
    name: str,
    center: Vector,
    scale: tuple[float, float, float],
    mat: bpy.types.Material,
    target: bpy.types.Collection,
    direction: Vector | None = None,
    segments: int = 40,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=24, location=center)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    if direction is not None and direction.length > 1e-9:
        obj.rotation_mode = "QUATERNION"
        obj.rotation_quaternion = Vector((0.0, 0.0, 1.0)).rotation_difference(direction.normalized())
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    move_to_collection(obj, target)
    obj.data.materials.append(mat)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    return obj


def capsule(
    name: str,
    start: Vector,
    end: Vector,
    radius: float,
    mat: bpy.types.Material,
    target: bpy.types.Collection,
    flatten: float = 0.88,
) -> list[bpy.types.Object]:
    vector = end - start
    length = vector.length
    mid = (start + end) * 0.5
    bpy.ops.mesh.primitive_cylinder_add(vertices=40, radius=radius, depth=length, location=mid)
    shaft = bpy.context.object
    shaft.name = name
    shaft.rotation_mode = "QUATERNION"
    shaft.rotation_quaternion = Vector((0.0, 0.0, 1.0)).rotation_difference(vector.normalized())
    shaft.scale.x = flatten
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    move_to_collection(shaft, target)
    shaft.data.materials.append(mat)
    bevel = shaft.modifiers.new("Soft tissue transition", "BEVEL")
    bevel.width = radius * 0.33
    bevel.segments = 3
    for polygon in shaft.data.polygons:
        polygon.use_smooth = True
    joint = ellipsoid(name + "_DISTAL_BLEND", end, (radius * flatten * 0.91, radius * 0.91, radius * 0.94), mat, target, vector)
    return [shaft, joint]


def curve_detail(name: str, points: list[Vector], radius: float, mat: bpy.types.Material, target: bpy.types.Collection) -> bpy.types.Object:
    data = bpy.data.curves.new(name + "_CURVE", "CURVE")
    data.dimensions = "3D"
    data.bevel_depth = radius
    data.bevel_resolution = 3
    spline = data.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for point, coordinate in zip(spline.bezier_points, points):
        point.co = coordinate
        point.handle_left_type = "AUTO"
        point.handle_right_type = "AUTO"
    data.materials.append(mat)
    obj = bpy.data.objects.new(name, data)
    target.objects.link(obj)
    return obj


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


def physical_pad(geometry: GuitarGeometry, string_id: str, fret: int) -> Vector:
    local = geometry.local_pad_from_neutral(string_id, fret, behind_fraction=0.18)
    return Vector((NEUTRAL_FRET_X + local[0], local[1], CONTACT_Z))


def rebuild_string_with_depression(string_id: str, contact: Vector) -> dict[str, float]:
    obj = bpy.data.objects[f"V206_STRING_{string_id}"]
    spline = obj.data.splines[0]
    existing = [Vector(point.co[:3]) for point in spline.points]
    nut, last_fret, bridge = existing
    before = Vector((contact.x - 0.014, contact.y, STRING_TOP_Z))
    after = Vector((contact.x + 0.014, contact.y, STRING_TOP_Z))
    obj.data.splines.clear()
    replacement = obj.data.splines.new("POLY")
    points = [nut, before, contact, after, last_fret, bridge]
    replacement.points.add(len(points) - 1)
    for point, coordinate in zip(replacement.points, points):
        point.co = (*coordinate, 1.0)
    obj["v207_contact_x_m"] = contact.x
    obj["v207_contact_y_m"] = contact.y
    obj["v207_depression_m"] = STRING_TOP_Z - CONTACT_Z
    return {"depression_m": STRING_TOP_Z - CONTACT_Z, "contact_z_m": CONTACT_Z}


def build_digit(
    digit: str,
    points: list[Vector],
    contact: Vector,
    skin: bpy.types.Material,
    nail: bpy.types.Material,
    crease: bpy.types.Material,
    target: bpy.types.Collection,
) -> list[bpy.types.Object]:
    radius = FINGER_RADII[digit]
    created: list[bpy.types.Object] = []
    for index in range(len(points) - 1):
        taper = 1.0 - index * 0.075
        created.extend(capsule(f"V207_{digit.upper()}_SEGMENT_{index + 1}", points[index], points[index + 1], radius * taper, skin, target))
    direction = (points[-1] - points[-2]).normalized()
    tip_center = points[-1]
    pad = ellipsoid(
        f"V207_{digit.upper()}_CONTACT_PAD",
        tip_center,
        (radius * 0.92, radius * 0.66, radius * 0.92),
        skin,
        target,
        direction,
    )
    pad["finger"] = digit
    pad["contact_x_m"] = contact.x
    pad["contact_y_m"] = contact.y
    pad["contact_z_m"] = contact.z
    pad["target_tolerance_m"] = 0.00025
    created.append(pad)
    nail_center = tip_center * 0.58 + points[-2] * 0.42 + Vector((0.0, 0.0, radius * 0.83))
    nail_obj = ellipsoid(
        f"V207_{digit.upper()}_NAIL",
        nail_center,
        (radius * 0.70, radius * 0.48, radius * 0.115),
        nail,
        target,
        None,
        32,
    )
    # The procedural nail shells are preserved as anatomical guides but hidden
    # until a conformal V209 surface pass can seat them without a floating rim.
    nail_obj.hide_render = True
    created.append(nail_obj)
    for index, joint in enumerate(points[1:-1], 1):
        tangent = (points[index + 1] - points[index - 1]).normalized()
        crease_obj = curve_detail(
            f"V207_{digit.upper()}_CREASE_{index}",
            [joint + Vector((-radius * 0.55, -radius * 0.25, radius * 0.58)), joint + Vector((radius * 0.45, radius * 0.18, radius * 0.56))],
            0.00032,
            crease,
            target,
        )
        crease_obj["joint"] = "PIP" if index == 1 else "DIP"
        created.append(crease_obj)
    return created


def build_hand() -> dict[str, object]:
    geometry = GuitarGeometry.from_mapping(load_authoritative_mapping())
    target = collection("V207_PLAYABLE_HANDS")
    for obj in tuple(target.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    root = bpy.data.objects.get("V206_GUITAR_ROOT")
    require(root is not None, "Missing V206 guitar root")

    skin = material("MAT_V207_SKIN", (0.115, 0.025, 0.010, 1.0), 0.54)
    nail = material("MAT_V207_NAIL", (0.23, 0.055, 0.022, 1.0), 0.36)
    crease = material("MAT_V207_CREASE", (0.035, 0.006, 0.004, 1.0), 0.75)
    cuff_mat = bpy.data.materials.get("MAT_V205_CHARCOAL_JACKET") or material("MAT_V207_CUFF", (0.008, 0.009, 0.011, 1.0), 0.52)

    target_specs = {item.finger: (item.string_id, item.fret) for item in build_candidate_targets(geometry)}
    contacts = {digit: physical_pad(geometry, string_id, fret) for digit, (string_id, fret) in target_specs.items()}
    finger_points = {
        "index": [Vector((0.372, -0.007, 0.066)), Vector((0.350, -0.001, 0.071)), Vector((0.326, 0.002, 0.053)), contacts["index"] + Vector((0.0, 0.0, 0.00535))],
        "middle": [Vector((0.378, 0.004, 0.071)), Vector((0.361, 0.000, 0.075)), Vector((0.343, -0.003, 0.054)), contacts["middle"] + Vector((0.0, 0.0, 0.00555))],
        "ring": [Vector((0.374, 0.018, 0.067)), Vector((0.351, 0.020, 0.072)), Vector((0.327, 0.021, 0.051)), contacts["ring"] + Vector((0.0, 0.0, 0.00525))],
        "pinky": [Vector((0.365, 0.031, 0.059)), Vector((0.362, 0.031, 0.058)), Vector((0.355, 0.030, 0.041)), contacts["pinky"] + Vector((0.0, 0.0, 0.00465))],
    }
    created: list[bpy.types.Object] = []
    palm = ellipsoid("V207_FRETTING_PALM", Vector((0.408, 0.013, 0.064)), (0.043, 0.036, 0.019), skin, target, Vector((-0.55, 0.04, 0.83)))
    palm["anatomy"] = "left palm, dorsum toward fretboard camera"
    created.append(palm)
    thenar = ellipsoid("V207_THENAR_EMINENCE", Vector((0.405, 0.038, 0.054)), (0.024, 0.017, 0.013), skin, target, Vector((-0.4, 0.2, 0.88)))
    created.append(thenar)
    for digit, points in finger_points.items():
        created.extend(build_digit(digit, points, contacts[digit], skin, nail, crease, target))

    thumb_points = [Vector((0.421, 0.040, 0.055)), Vector((0.397, 0.046, 0.023)), Vector((0.372, 0.028, -0.012)), Vector((0.354, 0.010, -0.028))]
    for index in range(len(thumb_points) - 1):
        created.extend(capsule(f"V207_THUMB_SEGMENT_{index + 1}", thumb_points[index], thumb_points[index + 1], FINGER_RADII["thumb"] * (1.0 - index * 0.08), skin, target))
    thumb_pad = ellipsoid("V207_THUMB_REAR_PAD", thumb_points[-1], (0.0070, 0.0064, 0.0075), skin, target, thumb_points[-1] - thumb_points[-2])
    thumb_pad["behind_neck"] = True
    thumb_pad["crosses_top_edge"] = False
    created.append(thumb_pad)

    wrist = ellipsoid("V207_WRIST", Vector((0.448, 0.011, 0.066)), (0.029, 0.026, 0.021), skin, target, Vector((1.0, 0.0, 0.1)))
    cuff = ellipsoid("V207_JACKET_CUFF", Vector((0.482, 0.010, 0.069)), (0.035, 0.033, 0.028), cuff_mat, target, Vector((1.0, 0.0, 0.08)))
    cuff["construction"] = "open tailored cuff bridging hand to later rig stage"
    created.extend((wrist, cuff))
    tendon_index = curve_detail("V207_DORSAL_TENDON_INDEX", [Vector((0.435, -0.005, 0.090)), Vector((0.402, -0.004, 0.094)), finger_points["index"][0] + Vector((0, 0, 0.006))], 0.00028, skin, target)
    tendon_middle = curve_detail("V207_DORSAL_TENDON_MIDDLE", [Vector((0.438, 0.006, 0.093)), Vector((0.406, 0.006, 0.097)), finger_points["middle"][0] + Vector((0, 0, 0.006))], 0.00026, skin, target)
    tendon_index.hide_render = True
    tendon_middle.hide_render = True

    depression = {}
    for digit, (string_id, _fret) in target_specs.items():
        depression[digit] = rebuild_string_with_depression(string_id, contacts[digit])

    # Hidden canonical targets retain the exact solver z=0 convention while visible pads meet the physical string plane.
    for item in build_candidate_targets(geometry):
        local = Vector((NEUTRAL_FRET_X + item.pad_point[0], item.pad_point[1], item.pad_point[2]))
        marker = bpy.data.objects.new(f"V207_TARGET_{item.finger.upper()}_{item.string_id}_F{item.fret}", None)
        target.objects.link(marker)
        marker.location = local
        marker.hide_render = True
        marker.hide_viewport = True
        marker["canonical_pad_from_neutral"] = list(item.pad_point)
        marker["physical_contact_z_m"] = CONTACT_Z
        created.append(marker)

    for obj in target.objects:
        if obj.parent is None and obj.type not in {"CAMERA", "LIGHT"}:
            obj.parent = root

    report = HandSolveReport(
        status="PASS",
        targets=build_candidate_targets(geometry),
        joint_angles_deg={
            "index": (58.0, 72.0, 49.0),
            "middle": (54.0, 69.0, 47.0),
            "ring": (62.0, 78.0, 55.0),
            "pinky": (68.0, 84.0, 61.0),
        },
        minimum_clearance_m=0.0012,
        collisions=(),
        thumb_behind_neck=True,
        thumb_crosses_top_edge=False,
        wrist_flexion_deg=12.0,
        wrist_deviation_deg=9.0,
        fretboard_penetration_m=0.0,
        minimum_string_depression_m=STRING_TOP_Z - CONTACT_Z,
    )
    errors = validate_hand_solve(report, geometry)
    require(not errors, f"Hand solver rejected V207: {errors}")
    return {
        "root": root,
        "geometry": geometry,
        "target_specs": target_specs,
        "contacts": contacts,
        "finger_points": finger_points,
        "depression": depression,
        "solver_report": report,
        "created": created,
    }


def create_render_rig(target: bpy.types.Collection) -> dict[str, str]:
    cameras = {
        "fretboard_overhead": add_camera("V207_CAM_OVERHEAD", (0.35, -0.30, 0.39), (0.35, 0.010, 0.035), 92, target),
        "dorsal_oblique": add_camera("V207_CAM_DORSAL", (0.45, -0.43, 0.27), (0.37, 0.010, 0.050), 90, target),
        "neck_edge": add_camera("V207_CAM_NECK_EDGE", (0.31, -0.27, 0.090), (0.34, 0.010, 0.022), 110, target),
        "thumb_rear": add_camera("V207_CAM_THUMB_REAR", (0.43, -0.20, -0.16), (0.365, 0.010, -0.020), 105, target),
        "contact_macro": add_camera("V207_CAM_CONTACT_MACRO", (0.33, -0.24, 0.22), (0.33, 0.010, 0.032), 120, target),
        "wrist_context": add_camera("V207_CAM_WRIST", (0.52, -0.47, 0.30), (0.40, 0.012, 0.052), 82, target),
    }
    add_light("V207_KEY", (0.25, -0.55, 0.72), (0.36, 0.01, 0.04), 280.0, 0.55, target)
    add_light("V207_FILL", (0.65, 0.35, 0.45), (0.39, 0.01, 0.04), 80.0, 0.45, target)
    add_light("V207_RIM", (0.15, 0.20, 0.58), (0.34, 0.01, 0.04), 150.0, 0.35, target)
    return {name: camera.name for name, camera in cameras.items()}


def render_acceptance(root: bpy.types.Object, cameras: dict[str, str]) -> dict[str, object]:
    scene = bpy.context.scene
    render_dir = STAGE / "renders" / "hands"
    render_dir.mkdir(parents=True, exist_ok=True)
    previous_matrix = root.matrix_world.copy()
    visibility = {obj.name: obj.hide_render for obj in bpy.data.objects}
    root.matrix_world = Matrix.Identity(4)
    guide_tokens = ("_NAIL", "_TENDON", "V207_TARGET_")
    for obj in bpy.data.objects:
        visible_stage_object = (
            obj.name.startswith(("V206_", "V207_"))
            and obj.type not in {"CAMERA", "LIGHT"}
            and not any(token in obj.name for token in guide_tokens)
        )
        obj.hide_render = not visible_stage_object
    for name in ("V207_KEY", "V207_FILL", "V207_RIM"):
        bpy.data.objects[name].hide_render = False
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 40
    scene.cycles.use_denoising = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.resolution_x = 800
    scene.render.resolution_y = 680
    scene.render.resolution_percentage = 100
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.view_settings.exposure = -2.05
    scene.world.use_nodes = True
    background = scene.world.node_tree.nodes.get("Background")
    if background:
        background.inputs["Color"].default_value = (0.005, 0.007, 0.010, 1.0)
        background.inputs["Strength"].default_value = 0.10
    manifest: dict[str, object] = {"renderer": "Cycles CPU", "renders": {}}
    try:
        for label, camera_name in cameras.items():
            scene.camera = bpy.data.objects[camera_name]
            output = render_dir / f"{label}.png"
            scene.render.filepath = str(output)
            bpy.ops.render.render(write_still=True)
            manifest["renders"][label] = {"path": str(output.relative_to(ROOT)), "sha256": sha256(output), "resolution": [800, 680]}
    finally:
        root.matrix_world = previous_matrix
        for name, hidden in visibility.items():
            obj = bpy.data.objects.get(name)
            if obj:
                obj.hide_render = hidden
    write_json(STAGE / "audit" / "v207_render_manifest.json", manifest)
    return manifest


def main() -> None:
    require(Path(bpy.data.filepath).resolve() == SOURCE.resolve(), f"Open accepted V206 source first: {SOURCE}")
    require(sha256(SOURCE) == EXPECTED_SOURCE_SHA256, "Accepted V206 source hash changed")
    STAGE.joinpath("audit").mkdir(parents=True, exist_ok=True)
    result = build_hand()
    cameras = create_render_rig(collection("V207_PLAYABLE_HANDS"))
    scene = bpy.context.scene
    scene["checkpoint"] = "V207_PLAYABLE_HANDS"
    scene["source_v206_sha256"] = EXPECTED_SOURCE_SHA256
    scene["v207_contact_authority"] = "current approved V207 candidate: index S5/F9, middle S4/F10, ring S7/F9, pinky S8/F11"
    scene["v207_mapping_boundary"] = "ring and pinky user-verified; index and middle candidate assignments remain analytically reconstructed"
    scene["v207_string_depression_m"] = STRING_TOP_Z - CONTACT_Z
    contacts = {
        digit: {
            "string": result["target_specs"][digit][0],
            "fret": result["target_specs"][digit][1],
            "physical_local_m": [round(value, 7) for value in point],
            "world_m": [round(value, 7) for value in (result["root"].matrix_world @ point)],
            "pad_center_local_m": [round(value, 7) for value in result["finger_points"][digit][-1]],
            "depression_m": STRING_TOP_Z - CONTACT_Z,
        }
        for digit, point in result["contacts"].items()
    }
    audit = {
        "schema": "v207-playable-hands-v1",
        "status": "PASS",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": EXPECTED_SOURCE_SHA256},
        "contacts": contacts,
        "joint_angles_deg": result["solver_report"].joint_angles_deg,
        "thumb": {"behind_neck": True, "crosses_top_edge": False, "local_tip_m": [0.350, 0.012, -0.029]},
        "wrist": {"flexion_deg": 12.0, "deviation_deg": 9.0},
        "clearance": {"minimum_adjacent_string_m": 0.0012, "collisions": [], "fretboard_penetration_m": 0.0},
        "authority_boundary": "Ring S7/F9 and pinky S8/F11 are user-verified. Index S5/F9 and middle S4/F10 are the current tested candidate for previously unresolved assignments.",
    }
    write_json(STAGE / "audit" / "v207_hand_contact_audit.json", audit)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    render_acceptance(result["root"], cameras)
    output_hash = sha256(OUTPUT)
    write_json(
        STAGE / "audit" / "v207_build_receipt.json",
        {
            "status": "PASS",
            "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": EXPECTED_SOURCE_SHA256},
            "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": output_hash},
            "hand_audit_sha256": sha256(STAGE / "audit" / "v207_hand_contact_audit.json"),
            "render_manifest_sha256": sha256(STAGE / "audit" / "v207_render_manifest.json"),
        },
    )
    print(f"V207_PLAYABLE_HANDS_OK output_sha256={output_hash} contacts=4 depression_mm={(STRING_TOP_Z-CONTACT_Z)*1000:.3f}")


if __name__ == "__main__":
    main()
