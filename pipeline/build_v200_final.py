from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector


STAGE_ROOT = Path(__file__).resolve().parents[1]
if str(STAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(STAGE_ROOT))

from pipeline.common import _fingerprint_object, sha256, write_json
from pipeline.rendering import BODY_CAMERAS, HEAD_CAMERAS, render_group


EXPECTED_V192_SHA256 = "443321b43df4ada529113854f935b393e2e523fbbd36beb08c53fb0d08048148"
CONTACT_NAMES = (
    "V166_PICK",
    "V196_FRETTING_INDEX",
    "V196_FRETTING_MIDDLE",
    "V196_FRETTING_RING",
    "V196_FRETTING_PINKY",
    "V196_PICKING_THUMB",
    "V196_PICKING_INDEX",
)
AUDITS = {
    "V194": "production_v194_identity/audit/v194_identity_audit.json",
    "V195": "production_v195_wardrobe/audit/v195_wardrobe_audit.json",
    "V196": "production_v196_hands/audit/v196_hand_contact_audit.json",
    "V197": "production_v197_rig/audit/v197_rig_audit.json",
    "V198": "production_v198_deformation/audit/v198_deformation_audit.json",
    "V199": "production_v199_lookdev/audit/v199_lookdev_audit.json",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--rollback", type=Path, required=True)
    parser.add_argument("--stage-root", type=Path, default=STAGE_ROOT)
    return parser.parse_args(sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else [])


def matrices_record() -> dict[str, list[float]]:
    return {
        name: [round(float(value), 8) for row in bpy.data.objects[name].matrix_world for value in row]
        for name in CONTACT_NAMES
    }


def record_hash(record: dict[str, list[float]]) -> str:
    payload = json.dumps(record, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def guitar_fingerprint() -> dict[str, object]:
    records = [
        _fingerprint_object(obj)
        for obj in sorted(bpy.data.objects, key=lambda item: item.name)
        if obj.name == "V166_PICK" or obj.name.startswith("ANTV1_")
    ]
    payload = json.dumps(records, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {"count": len(records), "sha256": hashlib.sha256(payload).hexdigest()}


def audit_verdict(payload: dict[str, object]) -> str:
    evidence: list[str] = []
    if payload.get("verdict") is not None:
        evidence.append(str(payload["verdict"]))
    validation = payload.get("validation")
    if isinstance(validation, dict):
        evidence.extend(str(value) for value in validation.values())
    if payload.get("reopen_validation") is not None:
        evidence.append(str(payload["reopen_validation"]))
    visual = payload.get("visual_review")
    if visual in {"PASS", "FAIL"}:
        evidence.append(str(visual))
    return "PASS" if evidence and all(value == "PASS" for value in evidence) else "FAIL"


def load_prior_audits(stage_root: Path) -> dict[str, dict[str, object]]:
    records: dict[str, dict[str, object]] = {}
    for checkpoint, relative in AUDITS.items():
        path = stage_root / relative
        if not path.is_file():
            raise RuntimeError(f"Missing prior audit: {path}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        records[checkpoint] = {
            "path": relative,
            "sha256": sha256(path),
            "schema": payload.get("schema"),
            "verdict": audit_verdict(payload),
        }
    failed = [checkpoint for checkpoint, record in records.items() if record["verdict"] != "PASS"]
    if failed:
        raise RuntimeError(f"Prior audit gate failed: {failed}")
    return records


def material_slot(obj: bpy.types.Object, material: bpy.types.Material) -> int:
    for index, slot in enumerate(obj.material_slots):
        if slot.material == material:
            return index
    obj.data.materials.append(material)
    return len(obj.material_slots) - 1


def tune_ramp(
    material_name: str,
    dark: tuple[float, float, float, float],
    light: tuple[float, float, float, float],
    roughness: float,
) -> None:
    material = bpy.data.materials[material_name]
    principled = material.node_tree.nodes.get("Principled BSDF")
    if principled:
        principled.inputs["Roughness"].default_value = roughness
    ramps = [node for node in material.node_tree.nodes if node.type == "VALTORGB"]
    if ramps:
        ramps[0].color_ramp.elements[0].color = dark
        ramps[0].color_ramp.elements[-1].color = light
    material["v200_final_tuned"] = True


def smoothstep(edge0: float, edge1: float, value: float) -> float:
    if edge0 == edge1:
        return float(value >= edge1)
    t = max(0.0, min(1.0, (value - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def build_face_beard_shader() -> int:
    head = bpy.data.objects["V194_HEAD"]
    skin = bpy.data.materials["V199_SKIN_MAT"]
    attribute_name = "V200_BEARD_MASK"
    existing = head.data.attributes.get(attribute_name)
    if existing:
        head.data.attributes.remove(existing)
    attribute = head.data.attributes.new(attribute_name, type="FLOAT", domain="POINT")
    nonzero = 0
    for vertex in head.data.vertices:
        world = head.matrix_world @ vertex.co
        side = min(1.0, abs(world.x) / 0.090)
        upper = 1.646 + 0.038 * side
        lower_mask = smoothstep(1.548, 1.566, world.z)
        upper_mask = 1.0 - smoothstep(upper - 0.008, upper + 0.006, world.z)
        front_mask = 1.0 - smoothstep(0.020, 0.065, world.y)
        central = 1.0 - smoothstep(0.037, 0.052, abs(world.x))
        mouth_band = smoothstep(1.586, 1.602, world.z) * (1.0 - smoothstep(1.638, 1.650, world.z))
        mouth_front = 1.0 - smoothstep(-0.015, 0.030, world.y)
        mask = lower_mask * upper_mask * front_mask * (1.0 - central * mouth_band * mouth_front)
        attribute.data[vertex.index].value = mask
        nonzero += int(mask > 0.001)

    face = bpy.data.materials.get("V200_FACE_SKIN_BEARD_MAT")
    if face is None:
        face = skin.copy()
        face.name = "V200_FACE_SKIN_BEARD_MAT"
    face.use_nodes = True
    nodes = face.node_tree.nodes
    links = face.node_tree.links
    for node in list(nodes):
        if node.name.startswith("V200 Beard"):
            nodes.remove(node)
    principled = nodes.get("Principled BSDF")
    if principled is None:
        raise RuntimeError("V200 face shader needs Principled BSDF")
    base = principled.inputs["Base Color"]
    prior_socket = None
    if base.is_linked:
        prior_socket = base.links[0].from_socket
        links.remove(base.links[0])
    attribute_node = nodes.new("ShaderNodeAttribute")
    attribute_node.name = "V200 Beard Mask"
    attribute_node.attribute_name = attribute_name
    attribute_node.location = (-260, 260)
    texcoord = nodes.new("ShaderNodeTexCoord")
    texcoord.name = "V200 Beard Coordinates"
    texcoord.location = (-760, 420)
    noise = nodes.new("ShaderNodeTexNoise")
    noise.name = "V200 Beard Microtexture"
    noise.location = (-560, 420)
    noise.inputs["Scale"].default_value = 145.0
    noise.inputs["Detail"].default_value = 4.0
    noise.inputs["Roughness"].default_value = 0.74
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.name = "V200 Beard Color"
    ramp.location = (-340, 470)
    ramp.color_ramp.elements[0].color = (0.0015, 0.00045, 0.00018, 1.0)
    ramp.color_ramp.elements[-1].color = (0.025, 0.007, 0.0022, 1.0)
    mix = nodes.new("ShaderNodeMixRGB")
    mix.name = "V200 Beard Surface Blend"
    mix.blend_type = "MIX"
    mix.location = (0, 180)
    if prior_socket:
        links.new(prior_socket, mix.inputs[1])
    else:
        mix.inputs[1].default_value = base.default_value
    links.new(texcoord.outputs["Generated"], noise.inputs["Vector"])
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], mix.inputs[2])
    links.new(attribute_node.outputs["Fac"], mix.inputs[0])
    links.new(mix.outputs["Color"], base)
    head.data.materials.clear()
    head.data.materials.append(face)
    old_beard = bpy.data.objects.get("V194_BEARD")
    if old_beard:
        old_beard.hide_render = True
        old_beard.hide_viewport = True
        old_beard["v200_replaced_by_surface_material"] = True
    return nonzero


def build_hair_part_line() -> list[str]:
    hair_material = bpy.data.materials["V199_HAIR_MAT"]
    rig = bpy.data.objects["V197_RIG"]
    center_y = 0.001
    center_z = 1.694
    radius_x = 0.097 * 1.055
    radius_y = 0.086 * 1.065
    radius_z = 0.126 * 1.045
    part_skin = bpy.data.materials.get("V200_HAIR_PART_SKIN_MAT") or bpy.data.materials.new("V200_HAIR_PART_SKIN_MAT")
    part_skin.use_nodes = True
    part_skin.diffuse_color = (0.105, 0.030, 0.009, 1.0)
    principled = part_skin.node_tree.nodes.get("Principled BSDF")
    if principled:
        principled.inputs["Base Color"].default_value = (0.105, 0.030, 0.009, 1.0)
        principled.inputs["Roughness"].default_value = 0.65

    base_points: list[tuple[float, float]] = []
    for index in range(9):
        z = 1.744 + 0.052 * index / 8.0
        part_x = 0.036 + 0.20 * (z - 1.75)
        base_points.append((part_x, z))

    created: list[str] = []
    for name, material, half_width, offset in (
        ("V200_HAIR_PART_COVER", hair_material, 0.0070, -0.0040),
        ("V200_HAIR_PART_LINE", part_skin, 0.00115, -0.0048),
    ):
        vertices: list[tuple[float, float, float]] = []
        for part_x, z in base_points:
            for x in (part_x - half_width, part_x + half_width):
                term = max(0.0, 1.0 - (x / radius_x) ** 2 - ((z - center_z) / radius_z) ** 2)
                y = center_y - radius_y * term**0.5 + offset
                vertices.append((x, y, z))
        faces = [(2 * row, 2 * row + 2, 2 * row + 3, 2 * row + 1) for row in range(len(base_points) - 1)]
        mesh = bpy.data.meshes.new(name + "_DATA")
        mesh.from_pydata(vertices, [], faces)
        mesh.update()
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.scene.collection.objects.link(obj)
        mesh.materials.append(material)
        for polygon in mesh.polygons:
            polygon.use_smooth = True
        world = obj.matrix_world.copy()
        obj.parent = rig
        obj.parent_type = "BONE"
        obj.parent_bone = "head"
        obj.matrix_world = world
        created.append(obj.name)
    return created


def archive_replaced_details() -> list[str]:
    names = (
        "ANTV25_FRETTING_SLEEVE",
        "V119_SURFACE_HINGED_LAPEL_PANELS",
        "V123_POCKET_FLAP_SEAM",
        "V123_POCKET_U_SEAM",
        "V127_ANATOMICAL_LEFT_LOWER_WELT_SEAM",
        "V127_ANATOMICAL_RIGHT_LOWER_WELT_SEAM",
        "V133_ANATOMICAL_LEFT_PLACKET_SEAM",
        "V133_ANATOMICAL_RIGHT_PLACKET_SEAM",
        "V149_REAR_NECK_WRIST_BRIDGE",
        "V176_LOW_HEEL_LEFT",
        "V176_LOW_HEEL_RIGHT",
        "V176_MATCHED_OUTSOLE_LEFT",
        "V176_MATCHED_OUTSOLE_RIGHT",
        "V193_TAPERED_PICKING_SLEEVE",
        "V90_CHELSEA_GUSSET_ANATOMICAL_LEFT",
        "V90_CHELSEA_GUSSET_ANATOMICAL_RIGHT",
    )
    archived: list[str] = []
    for name in names:
        obj = bpy.data.objects.get(name)
        if obj is None:
            continue
        obj.hide_render = True
        obj.hide_viewport = True
        obj["v200_archived_replaced_detail"] = True
        archived.append(name)
    return archived


def cover_wardrobe_underlayer() -> int:
    body = bpy.data.objects["V195_BODY"]
    skin = bpy.data.materials["V199_SKIN_MAT"]
    shirt = bpy.data.materials["V199_SHIRT_MAT"]
    skin_index = material_slot(body, skin)
    shirt_index = material_slot(body, shirt)
    assigned = 0
    for polygon in body.data.polygons:
        center = sum((body.data.vertices[index].co for index in polygon.vertices), Vector()) / len(polygon.vertices)
        world = body.matrix_world @ center
        is_underlayer = 1.015 < world.z < 1.475 and abs(world.x) < 0.235 and world.y < 0.030
        polygon.material_index = shirt_index if is_underlayer else skin_index
        assigned += int(is_underlayer)
    body["v200_shirt_underlayer_polygons"] = assigned
    return assigned


def refine_boot_elastic() -> dict[str, dict[str, object]]:
    records: dict[str, dict[str, object]] = {}
    for suffix, x in (("L", 0.270), ("R", -0.270)):
        obj = bpy.data.objects[f"V195_BOOT_ELASTIC_{suffix}"]
        obj.location.x = x
        obj.location.y = -0.026
        obj.location.z = 0.167
        obj.scale.y *= 0.72
        obj.scale.z *= 0.76
        obj["v200_flush_side_insert"] = True
        records[obj.name] = {
            "location": [round(float(value), 6) for value in obj.location],
            "dimensions": [round(float(value), 6) for value in obj.dimensions],
        }
    return records


def refine_look() -> dict[str, object]:
    tune_ramp("V199_SKIN_MAT", (0.036, 0.009, 0.003, 1.0), (0.142, 0.043, 0.014, 1.0), 0.62)
    tune_ramp("V199_HAIR_MAT", (0.00008, 0.00006, 0.00004, 1.0), (0.0045, 0.0022, 0.0011, 1.0), 0.90)
    tune_ramp("V199_BEARD_MAT", (0.0015, 0.00045, 0.00018, 1.0), (0.025, 0.007, 0.0022, 1.0), 0.88)
    tune_ramp("V199_JACKET_MAT", (0.0015, 0.0020, 0.0026, 1.0), (0.016, 0.020, 0.025, 1.0), 0.80)
    tune_ramp("V199_BOOT_MAT", (0.012, 0.0025, 0.0008, 1.0), (0.078, 0.019, 0.0045, 1.0), 0.56)
    curl_detail = bpy.data.objects.get("V194_HAIR_CURL_DETAIL")
    if curl_detail:
        curl_detail.hide_render = True
        curl_detail.hide_viewport = True
        curl_detail["v200_replaced_by_material_microdetail"] = True
    lineset = bpy.context.scene.view_layers[0].freestyle_settings.linesets[0]
    lineset.select_silhouette = True
    lineset.select_external_contour = True
    lineset.select_border = False
    lineset.select_contour = False
    lineset.linestyle.thickness = 0.50
    lineset.linestyle.alpha = 0.65
    return {
        "beard_mask_vertices": build_face_beard_shader(),
        "shirt_underlayer_polygons": cover_wardrobe_underlayer(),
        "boot_elastic": refine_boot_elastic(),
        "hair_part_line": build_hair_part_line(),
        "archived_replaced_details": archive_replaced_details(),
        "hair_detail": "procedural material microdetail; bead overlay archived hidden",
        "contours": {"thickness_px": 0.50, "alpha": 0.65, "categories": ["silhouette", "external_contour"]},
    }


def missing_external_files() -> list[str]:
    missing: list[str] = []
    for image in bpy.data.images:
        if image.source != "FILE" or image.packed_file is not None or not image.filepath:
            continue
        path = Path(bpy.path.abspath(image.filepath))
        if not path.is_file():
            missing.append(f"image:{image.name}:{path}")
    for library in bpy.data.libraries:
        path = Path(bpy.path.abspath(library.filepath))
        if not path.is_file():
            missing.append(f"library:{library.name}:{path}")
    return sorted(missing)


def reset_shapes() -> None:
    for obj in bpy.data.objects:
        keys = getattr(obj.data, "shape_keys", None) if obj.data else None
        if keys:
            for key in keys.key_blocks:
                if key.name != "Basis":
                    key.value = 0.20 if key.name == "V198_CuffSeal" else 0.0


def set_action(name: str) -> None:
    rig = bpy.data.objects["V197_RIG"]
    rig.animation_data_create()
    rig.animation_data.action = bpy.data.actions[name]
    bpy.context.scene.frame_set(0)
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()


def set_shape(object_name: str, key_name: str, value: float) -> None:
    obj = bpy.data.objects[object_name]
    if obj.data.shape_keys and key_name in obj.data.shape_keys.key_blocks:
        obj.data.shape_keys.key_blocks[key_name].value = value


def set_guitar_visibility(hidden: bool) -> dict[str, bool]:
    previous: dict[str, bool] = {}
    for obj in bpy.data.objects:
        in_guitar_collection = any(collection.name == "ANT_STRANDBERG_BLOCKOUT" for collection in obj.users_collection)
        later_guitar_detail = obj.name.startswith("V178_") or obj.name == "V186_TAPERED_FACETED_ENDURNECK_BLOCKOUT"
        if obj.name == "V166_PICK" or in_guitar_collection or later_guitar_detail:
            previous[obj.name] = bool(obj.hide_render)
            obj.hide_render = hidden
    return previous


def restore_visibility(previous: dict[str, bool]) -> None:
    for name, hidden in previous.items():
        bpy.data.objects[name].hide_render = hidden


def render_manifest(stage_root: Path, outputs: dict[str, str], cameras: dict[str, str]) -> dict[str, dict[str, str]]:
    return {
        label: {
            "camera": cameras[label],
            "path": str(Path(path).relative_to(stage_root)),
            "sha256": sha256(Path(path)),
        }
        for label, path in outputs.items()
    }


def render_facial_controls(output: Path, directory: Path) -> dict[str, str]:
    scene = bpy.context.scene
    camera = bpy.data.objects["V95_CAM_HEAD_FRONT"]
    directory.mkdir(parents=True, exist_ok=True)
    scene.camera = camera
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 600
    scene.render.resolution_y = 600
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    outputs: dict[str, str] = {}
    controls = ("neutral", "blink", "tired_gaze", "ah")
    for control in controls:
        reset_shapes()
        if control == "blink":
            set_shape("V194_HEAD", "Blink", 1.0)
            for suffix in ("L", "R"):
                set_shape(f"V194_UPPER_LID_{suffix}", "Blink", 1.0)
                set_shape(f"V194_LOWER_LID_{suffix}", "Blink", 1.0)
        elif control == "tired_gaze":
            set_shape("V194_HEAD", "TiredGaze", 1.0)
        elif control == "ah":
            set_shape("V194_HEAD", "Ah", 1.0)
            set_shape("V194_MOUTH", "Ah", 1.0)
        bpy.context.view_layer.update()
        path = directory / f"{control}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        outputs[control] = str(path)
    reset_shapes()
    return outputs


def main() -> None:
    args = parse_args()
    source = args.source.resolve()
    output = args.output.resolve()
    rollback = args.rollback.resolve()
    stage_root = args.stage_root.resolve()
    if Path(bpy.data.filepath).resolve() != source:
        raise RuntimeError(f"Loaded source mismatch: {bpy.data.filepath} != {source}")
    if not rollback.is_file():
        raise RuntimeError(f"Missing V192 rollback: {rollback}")
    rollback_sha = sha256(rollback)
    if rollback_sha != EXPECTED_V192_SHA256:
        raise RuntimeError(f"V192 rollback hash mismatch: {rollback_sha}")

    output.parent.mkdir(parents=True, exist_ok=True)
    production = stage_root / "production_v200_final"
    prior_audits = load_prior_audits(stage_root)
    set_action("V197_PERFORMANCE_POSE")
    reset_shapes()
    contact_before = matrices_record()
    guitar_before = guitar_fingerprint()
    expected_guitar = bpy.context.scene.get("v196_guitar_fingerprint_after")
    if expected_guitar and guitar_before["sha256"] != expected_guitar:
        raise RuntimeError(f"Protected guitar baseline mismatch: {guitar_before['sha256']} != {expected_guitar}")

    visual_refinements = refine_look()
    missing = missing_external_files()
    if missing:
        raise RuntimeError("Missing external dependencies: " + ", ".join(missing))

    scene = bpy.context.scene
    scene.name = "Character Asset_An V200"
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    scene.unit_settings.length_unit = "METERS"
    scene.render.film_transparent = False
    try:
        scene.view_settings.look = "AgX - Medium High Contrast"
    except TypeError:
        pass
    scene["checkpoint"] = "V200"
    scene["checkpoint_intent"] = "final reference-locked animation-ready character delivery"
    scene["source_checkpoint"] = source.name
    scene["asset_name"] = "Character Asset_An"
    scene["asset_version"] = "V200"
    scene["asset_runtime"] = bpy.app.version_string
    scene["reference_authority"] = "approved_design_lock > turnaround_v2 > face_v2 > turnaround_v3"
    scene["v200_v192_sha256"] = rollback_sha
    scene["v200_prior_audits_verdict"] = "PASS"
    scene["v200_prior_audits_json"] = json.dumps(prior_audits, sort_keys=True, separators=(",", ":"))
    scene["v200_missing_external_files"] = len(missing)
    scene.camera = bpy.data.objects["V151_FRONT_CAMERA"]
    bpy.ops.wm.save_as_mainfile(filepath=str(output), check_existing=False)

    render_root = production / "renders"
    manifests: dict[str, object] = {}

    set_action("V197_NEUTRAL_POSE")
    reset_shapes()
    guitar_visibility = set_guitar_visibility(True)
    neutral_outputs = render_group(output, render_root / "neutral_turnaround", BODY_CAMERAS, (600, 720))
    manifests["neutral_turnaround"] = render_manifest(stage_root, neutral_outputs, BODY_CAMERAS)
    restore_visibility(guitar_visibility)

    set_action("V197_PERFORMANCE_POSE")
    reset_shapes()
    performance_outputs = render_group(output, render_root / "performance_orbit", BODY_CAMERAS, (600, 720))
    manifests["performance_orbit"] = render_manifest(stage_root, performance_outputs, BODY_CAMERAS)

    identity_outputs = render_group(output, render_root / "identity", HEAD_CAMERAS, (600, 600))
    manifests["identity"] = render_manifest(stage_root, identity_outputs, HEAD_CAMERAS)

    hand_cameras = {
        "fretting": "V142_FRETTING_CAMERA",
        "picking": "V166_PICKING_OBLIQUE_CAMERA",
    }
    hand_outputs = render_group(output, render_root / "hands", hand_cameras, (720, 720))
    manifests["hands"] = render_manifest(stage_root, hand_outputs, hand_cameras)

    wardrobe_cameras = {
        "torso_front": "V114_CAM_TORSO_FRONT",
        "front": BODY_CAMERAS["front"],
        "back": BODY_CAMERAS["back"],
        "lower_detail": "V89_CAM_LOWER_DETAIL",
    }
    wardrobe_outputs = render_group(output, render_root / "wardrobe", wardrobe_cameras, (720, 720))
    manifests["wardrobe"] = render_manifest(stage_root, wardrobe_outputs, wardrobe_cameras)

    facial_outputs = render_facial_controls(output, render_root / "facial_controls")
    facial_cameras = {label: "V95_CAM_HEAD_FRONT" for label in facial_outputs}
    manifests["facial_controls"] = render_manifest(stage_root, facial_outputs, facial_cameras)

    set_action("V197_PERFORMANCE_POSE")
    reset_shapes()
    scene.camera = bpy.data.objects["V151_FRONT_CAMERA"]
    bpy.context.view_layer.objects.active = bpy.data.objects["V197_RIG"]
    contact_after = matrices_record()
    guitar_after = guitar_fingerprint()
    if contact_before != contact_after:
        raise RuntimeError("Performance contact matrices changed during finalization")
    if guitar_before != guitar_after:
        raise RuntimeError("Protected guitar fingerprint changed during finalization")

    scene["v200_contact_fingerprint"] = record_hash(contact_after)
    scene["v200_contact_restore_verdict"] = "PASS"
    scene["v200_guitar_fingerprint"] = guitar_after["sha256"]
    scene["v200_guitar_restore_verdict"] = "PASS"
    scene["v200_active_action"] = "V197_PERFORMANCE_POSE"
    bpy.ops.wm.save_as_mainfile(filepath=str(output), check_existing=False)

    audit_path = production / "audit" / "v200_final_audit.json"
    write_json(
        audit_path,
        {
            "schema": "v200-final-audit",
            "source": str(source),
            "output": str(output),
            "source_sha256": sha256(source),
            "output_sha256": sha256(output),
            "runtime": bpy.app.version_string,
            "rollback": {"path": str(rollback), "sha256": rollback_sha, "verdict": "PASS"},
            "prior_audits": prior_audits,
            "visual_refinements": visual_refinements,
            "reference_locks": {
                "identity": "adult face, anatomical-left hair part, close beard, central mustache gap, tired off-axis gaze",
                "wardrobe": "dark floral shirt, charcoal work jacket, black rolled trousers, brown Chelsea boots",
                "performance": "guitar and both analytic hand-contact systems unchanged",
            },
            "dependencies": {"missing_external_files": missing, "procedural_or_packed": True},
            "contact": {
                "before": record_hash(contact_before),
                "after": record_hash(contact_after),
                "identical": contact_before == contact_after,
            },
            "guitar": {"before": guitar_before, "after": guitar_after, "identical": guitar_before == guitar_after},
            "renders": manifests,
            "validation": {"reopen": "pending", "structure": "pending", "archive": "pending"},
            "visual_review": "pending host contact-sheet review",
            "known_limits": [
                "Stylized modular construction is retained for the accepted performance-shot scale.",
                "V200 is saved by Blender 5.2.2 LTS and is not backward-compatible with Blender 4.5.",
            ],
        },
    )
    write_json(production / "renders" / "v200_render_manifest.json", {"schema": "v200-render-manifest-v1", "renders": manifests})
    status = production / "HEADLESS_BUILD_STATUS_V200.md"
    status.write_text(
        "# Character Asset_An — V200 Final\n\n"
        "V200 is the reference-locked, rigged, deformation-tested, painterly final character checkpoint. It retains the accepted Strandberg guitar and analytic fretting/picking contacts, while the final visual pass closes exposed torso gaps, integrates the beard into the facial surface, removes bead-like hair overlay clutter, and seats the Chelsea boot elastic panels.\n\n"
        f"- Runtime: `{bpy.app.version_string}`\n"
        f"- V192 rollback SHA-256: `{rollback_sha}`\n"
        f"- V200 SHA-256: `{sha256(output)}`\n"
        f"- Contact fingerprint: `{record_hash(contact_after)}` unchanged\n"
        f"- Guitar fingerprint: `{guitar_after['sha256']}` unchanged\n"
        "- Missing external dependencies: `0`\n"
        "- Guarded reopen/structural validation: pending\n"
        "- Final contact-sheet review: pending\n",
        encoding="utf-8",
    )
    print("V200_OUTPUT=" + str(output))


if __name__ == "__main__":
    main()
