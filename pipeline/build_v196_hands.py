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

from pipeline.common import _fingerprint_object, ensure_material, link_object_like, sha256, snapshot_objects, write_json
from pipeline.rendering import render_group


DIGITS = ("THUMB", "INDEX", "MIDDLE", "RING", "PINKY")
SOURCES = {
    "FRETTING": {
        "HAND": "V190_FRETTING_PALM_REAR",
        "THUMB": "V190_FRETTING_THUMB_REAR",
        "INDEX": "V190_FRETTING_INDEX",
        "MIDDLE": "V190_FRETTING_MIDDLE",
        "RING": "V190_FRETTING_RING",
        "PINKY": "V190_FRETTING_PINKY",
    },
    "PICKING": {
        "HAND": "V192_PICKING_PALM",
        "WRIST": "V192_PICKING_WRIST_BRIDGE",
        "THUMB": "V192_PICKING_THUMB",
        "INDEX": "V192_PICKING_INDEX",
        "MIDDLE": "V192_PICKING_MIDDLE",
        "RING": "V192_PICKING_RING",
        "PINKY": "V192_PICKING_PINKY",
    },
}
TARGETS = {name for group in SOURCES.values() for name in group.values()}


def activate(obj: bpy.types.Object) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def clone(source_name: str, new_name: str) -> bpy.types.Object:
    source = bpy.data.objects.get(source_name)
    if source is None:
        raise RuntimeError(f"Missing hand source: {source_name}")
    duplicate = source.copy()
    if source.data:
        duplicate.data = source.data.copy()
    duplicate.name = new_name
    duplicate.hide_render = False
    duplicate.hide_viewport = False
    link_object_like(source, duplicate)
    source.hide_render = True
    source.hide_viewport = True
    return duplicate


def selected_fingerprint(prefixes: tuple[str, ...], names: set[str]) -> dict[str, object]:
    records = [
        _fingerprint_object(obj)
        for obj in sorted(bpy.data.objects, key=lambda item: item.name)
        if obj.name in names or obj.name.startswith(prefixes)
    ]
    payload = json.dumps(records, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {"count": len(records), "sha256": hashlib.sha256(payload).hexdigest()}


def curve_points(obj: bpy.types.Object) -> list[Vector]:
    if obj.type != "CURVE" or not obj.data.splines:
        raise RuntimeError(f"Expected curve digit: {obj.name}")
    spline = obj.data.splines[0]
    if spline.type == "BEZIER":
        return [obj.matrix_world @ point.co for point in spline.bezier_points]
    return [obj.matrix_world @ Vector(point.co[:3]) for point in spline.points]


def add_ellipsoid(
    name: str,
    location: Vector,
    scale: tuple[float, float, float],
    material: bpy.types.Material,
    direction: Vector | None = None,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_uv_sphere_add(segments=28, ring_count=16, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    if direction is not None and direction.length > 0:
        obj.rotation_mode = "QUATERNION"
        obj.rotation_quaternion = Vector((0.0, 0.0, 1.0)).rotation_difference(direction.normalized())
    obj.data.materials.append(material)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    return obj


def add_crease(name: str, points: list[Vector], material: bpy.types.Material) -> bpy.types.Object:
    curve = bpy.data.curves.new(name + "_DATA", "CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth = 0.00055
    curve.bevel_resolution = 2
    spline = curve.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for point, coordinate in zip(spline.points, points):
        point.co = (*coordinate, 1.0)
    obj = bpy.data.objects.new(name, curve)
    bpy.context.scene.collection.objects.link(obj)
    curve.materials.append(material)
    return obj


def refine_palm(obj: bpy.types.Object) -> None:
    if obj.type != "MESH":
        return
    for polygon in obj.data.polygons:
        polygon.use_smooth = True


def refine_digit(
    hand: str,
    digit: str,
    obj: bpy.types.Object,
    skin: bpy.types.Material,
    nail: bpy.types.Material,
    created: list[bpy.types.Object],
) -> dict[str, object]:
    obj.data.bevel_resolution = max(4, obj.data.bevel_resolution)
    obj.data.resolution_u = max(8, obj.data.resolution_u)
    obj["contact_locked"] = True
    points = curve_points(obj)
    if len(points) < 2:
        raise RuntimeError(f"Insufficient digit controls: {obj.name}")
    tip = points[-1]
    direction = (tip - points[-2]).normalized()
    bevel = max(0.0045, float(obj.data.bevel_depth))
    pad = add_ellipsoid(
        f"V196_{hand}_{digit}_PAD",
        tip - direction * (bevel * 0.45),
        (bevel * 0.68, bevel * 0.58, bevel * 0.78),
        skin,
        direction,
    )
    nail_obj = add_ellipsoid(
        f"V196_{hand}_{digit}_NAIL",
        tip - direction * (bevel * 0.70) + Vector((0.0, -bevel * 0.62, 0.0)),
        (bevel * 0.52, bevel * 0.18, bevel * 0.72),
        nail,
        direction,
    )
    created.extend([pad, nail_obj])
    for index, point in enumerate(points[1:-1], start=1):
        previous = points[index - 1]
        following = points[index + 1]
        tangent = (following - previous).normalized()
        knuckle = add_ellipsoid(
            f"V196_{hand}_{digit}_KNUCKLE_{index:02d}",
            point,
            (bevel * 0.68, bevel * 0.62, bevel * 0.74),
            skin,
            tangent,
        )
        created.append(knuckle)
    return {"tip": [round(value, 7) for value in tip], "control_count": len(points), "bevel_depth": round(bevel, 7)}


def pick_center(obj: bpy.types.Object) -> Vector:
    if obj.type != "MESH" or not obj.data.vertices:
        raise RuntimeError("Protected pick must be a mesh")
    return sum((obj.matrix_world @ vertex.co for vertex in obj.data.vertices), Vector()) / len(obj.data.vertices)


def resolve_camera(preferred: str, tokens: tuple[str, ...]) -> str:
    obj = bpy.data.objects.get(preferred)
    if obj is not None and obj.type == "CAMERA":
        return preferred
    candidates = [
        item.name
        for item in bpy.data.objects
        if item.type == "CAMERA" and all(token in item.name.upper() for token in tokens)
    ]
    if not candidates:
        raise RuntimeError(f"No camera for {preferred} / {tokens}")
    return sorted(candidates)[0]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--stage-root", type=Path, default=STAGE_ROOT)
    return parser.parse_args(sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else [])


def main() -> None:
    args = parse_args()
    source = args.source.resolve()
    output = args.output.resolve()
    stage_root = args.stage_root.resolve()
    if Path(bpy.data.filepath).resolve() != source:
        raise RuntimeError(f"Loaded source mismatch: {bpy.data.filepath} != {source}")
    output.parent.mkdir(parents=True, exist_ok=True)
    protected_before = snapshot_objects(excluded=TARGETS, excluded_prefixes=("V196_",))
    guitar_before = selected_fingerprint(("ANTV1_",), {"V166_PICK"})

    skin = bpy.data.materials.get("ANT_MAT_SKIN") or bpy.data.materials.get("V194_SKIN_MAT")
    if skin is None:
        skin = ensure_material("V196_HAND_SKIN_MAT", (0.17, 0.055, 0.020, 1.0), 0.62)
    nail = ensure_material("V196_NAIL_MAT", (0.26, 0.095, 0.055, 1.0), 0.42)
    crease = ensure_material("V196_CREASE_MAT", (0.055, 0.012, 0.006, 1.0), 0.78)
    created: list[bpy.types.Object] = []
    digit_audit: dict[str, object] = {}
    for hand in ("FRETTING", "PICKING"):
        palm = clone(SOURCES[hand]["HAND"], f"V196_{hand}_HAND")
        refine_palm(palm)
        created.append(palm)
        digit_audit[hand.lower()] = {}
        for digit in DIGITS:
            obj = clone(SOURCES[hand][digit], f"V196_{hand}_{digit}")
            created.append(obj)
            digit_audit[hand.lower()][digit.lower()] = refine_digit(hand, digit, obj, skin, nail, created)
        corners = [palm.matrix_world @ Vector(corner) for corner in palm.bound_box]
        center = sum(corners, Vector()) / len(corners)
        extent_x = max(point.x for point in corners) - min(point.x for point in corners)
        crease_obj = add_crease(
                f"V196_{hand}_PALM_CREASE",
                [
                    center + Vector((-extent_x * 0.22, -0.017, 0.008)),
                    center + Vector((0.0, -0.019, -0.002)),
                    center + Vector((extent_x * 0.20, -0.017, -0.008)),
                ],
                crease,
            )
        crease_obj.hide_render = True
        created.append(crease_obj)
    wrist = clone(SOURCES["PICKING"]["WRIST"], "V196_PICKING_WRIST_BRIDGE")
    wrist.data.bevel_resolution = max(4, wrist.data.bevel_resolution)
    created.append(wrist)

    thumb_tip = curve_points(bpy.data.objects["V196_PICKING_THUMB"])[-1]
    index_tip = curve_points(bpy.data.objects["V196_PICKING_INDEX"])[-1]
    pinch_gap = (thumb_tip - index_tip).length
    midpoint_to_pick = ((thumb_tip + index_tip) * 0.5 - pick_center(bpy.data.objects["V166_PICK"])).length
    if abs(pinch_gap - 0.002468) > 0.0005:
        raise RuntimeError(f"Picking pinch drifted: {pinch_gap:.7f}")
    if abs(midpoint_to_pick - 0.002403) > 0.0005:
        raise RuntimeError(f"Picking midpoint drifted: {midpoint_to_pick:.7f}")

    guitar_after = selected_fingerprint(("ANTV1_",), {"V166_PICK"})
    protected_after = snapshot_objects(excluded=TARGETS, excluded_prefixes=("V196_",))
    if protected_before != protected_after:
        raise RuntimeError(f"Protected scene changed: {protected_before} != {protected_after}")
    if guitar_before != guitar_after:
        raise RuntimeError(f"Guitar fingerprint changed: {guitar_before} != {guitar_after}")

    scene = bpy.context.scene
    scene["checkpoint"] = "V196"
    scene["checkpoint_intent"] = "anatomical hand surfaces around locked fretting and picking contacts"
    scene["source_checkpoint"] = source.name
    scene["v196_pinch_gap_m"] = pinch_gap
    scene["v196_pinch_midpoint_to_pick_m"] = midpoint_to_pick
    scene["v196_guitar_fingerprint_before"] = guitar_before["sha256"]
    scene["v196_guitar_fingerprint_after"] = guitar_after["sha256"]
    bpy.ops.wm.save_as_mainfile(filepath=str(output), check_existing=False)

    cameras = {
        "fretting_oblique": resolve_camera("V142_FRETTING_CAMERA", ("FRETT",)),
        "picking_oblique": resolve_camera("V166_PICKING_OBLIQUE_CAMERA", ("PICK", "OBLIQUE")),
        "picking_player_edge": resolve_camera("V166_PICKING_PLAYER_EDGE_CAMERA", ("PICK", "PLAYER", "EDGE")),
    }
    optional = {
        "picking_canonical": ("V148_CANONICAL_HAND_CAMERA", ("CANONICAL", "HAND")),
        "picking_hand_oblique": ("V148_HAND_OBLIQUE_CAMERA", ("HAND", "OBLIQUE")),
    }
    for label, (preferred, tokens) in optional.items():
        try:
            cameras[label] = resolve_camera(preferred, tokens)
        except RuntimeError:
            pass
    production = stage_root / "production_v196_hands"
    render_dir = production / "renders" / "contacts"
    outputs = render_group(output, render_dir, cameras, (720, 720))
    render_manifest = {
        label: {"camera": cameras[label], "path": str(Path(path).relative_to(stage_root)), "sha256": sha256(Path(path))}
        for label, path in outputs.items()
    }
    audit_path = production / "audit" / "v196_hand_contact_audit.json"
    write_json(
        audit_path,
        {
            "schema": "v196-hand-contact-audit",
            "source": str(source),
            "output": str(output),
            "source_sha256": sha256(source),
            "output_sha256": sha256(output),
            "runtime": bpy.app.version_string,
            "created": sorted({obj.name for obj in created}),
            "hidden_predecessors": sorted(TARGETS),
            "digit_controls": digit_audit,
            "contact": {
                "thumb_index_gap_m": round(pinch_gap, 7),
                "pinch_midpoint_to_pick_center_m": round(midpoint_to_pick, 7),
                "fretting_thumb": "rear-hidden",
            },
            "guitar": {"before": guitar_before, "after": guitar_after, "identical": guitar_before == guitar_after},
            "protected_before": protected_before,
            "protected_after": protected_after,
            "protected_identical": protected_before == protected_after,
            "renders": render_manifest,
            "delivery": {"status": "pending host-Python contact-sheet composition"},
        },
    )
    write_json(production / "renders" / "v196_render_manifest.json", {"schema": "v196-render-manifest-v1", "renders": render_manifest})
    status = production / "HEADLESS_BUILD_STATUS_V196.md"
    status.parent.mkdir(parents=True, exist_ok=True)
    status.write_text(
        "# Character Asset_An — V196 Hands\n\n"
        "V196 smooths both accepted contact hands, adds knuckle transitions, fingertip pads, nails, and restrained palm creases, and keeps every analytic contact point fixed.\n\n"
        f"- Thumb/index gap: `{pinch_gap:.7f} m`\n"
        f"- Pinch midpoint to pick: `{midpoint_to_pick:.7f} m`\n"
        f"- Guitar fingerprint: `{guitar_before['sha256']}` unchanged\n"
        "- Structural and reopen validation: pending\n",
        encoding="utf-8",
    )
    print("V196_OUTPUT=" + str(output))


if __name__ == "__main__":
    main()
