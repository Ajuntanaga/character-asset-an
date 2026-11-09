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

from pipeline.common import link_object_like, sha256, snapshot_objects, write_json
from pipeline.rendering import BODY_CAMERAS, render_group


TARGETS = {
    "V194_BODY_IDENTITY_BASE",
    "V193_SCULPTED_OPEN_JACKET",
    "V193_CONTOURED_FLORAL_SHIRT",
    "V193_ROLLED_OPEN_JACKET_COLLAR",
    "V193_TAILORED_PICKING_CUFF",
    "V143_L_POSE_SPACE_CUFF",
    "V143_R_POSE_SPACE_CUFF",
    "V148_CLEAN_TRUE_BLACK_TROUSERS",
    "V89_CONNECTED_ROLLED_CUFFS",
    "V90_CHELSEA_BOOT_ANATOMICAL_LEFT",
    "V90_CHELSEA_BOOT_ANATOMICAL_RIGHT",
    "V121_FLORAL_SHIRT_COLLAR",
    "V121_COLLAR_BUTTON",
    "V133_SEATED_SHIRT_COLLAR_STAND",
    "V123_CONFORMING_POCKET_PEN",
    "V123_POCKET_FLAP_SEAM",
    "V123_POCKET_U_SEAM",
    "V123_POCKET_PEN_CLIP",
    *{f"V83_SHIRT_BUTTON_{index:02d}" for index in range(1, 8)},
    *{f"V127_ANATOMICAL_RIGHT_JACKET_BUTTON_{index:02d}" for index in range(1, 5)},
}


def activate(obj: bpy.types.Object) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def smooth(obj: bpy.types.Object) -> None:
    if obj.type == "MESH":
        for polygon in obj.data.polygons:
            polygon.use_smooth = True


def clone(source_name: str, new_name: str) -> bpy.types.Object:
    source = bpy.data.objects.get(source_name)
    if source is None:
        raise RuntimeError(f"Missing wardrobe source: {source_name}")
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


def coords_hash(coords: list[tuple[float, float, float]]) -> str:
    payload = json.dumps(sorted(tuple(round(value, 7) for value in coordinate) for coordinate in coords), separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def protected_endpoint(vertex: bpy.types.MeshVertex) -> bool:
    return vertex.co.z > 1.10 and (vertex.co.x > 0.28 or vertex.co.x < -0.18)


def build_body() -> tuple[bpy.types.Object, dict[str, object]]:
    source = bpy.data.objects["V194_BODY_IDENTITY_BASE"]
    protected_before = [tuple(vertex.co) for vertex in source.data.vertices if protected_endpoint(vertex)]
    body = clone("V194_BODY_IDENTITY_BASE", "V195_BODY")
    for vertex in body.data.vertices:
        if protected_endpoint(vertex):
            continue
        z = vertex.co.z
        if 1.02 < z < 1.48 and abs(vertex.co.x) < 0.235:
            vertex.co.x *= 0.955
            if vertex.co.y < 0.0:
                vertex.co.y *= 0.975
        elif 0.30 < z <= 1.02:
            center = 0.13 if vertex.co.x >= 0.0 else -0.13
            if abs(vertex.co.x - center) < 0.145:
                vertex.co.x = center + (vertex.co.x - center) * 0.955
    body.data.update()
    protected_after = [tuple(vertex.co) for vertex in body.data.vertices if protected_endpoint(vertex)]
    before_hash = coords_hash(protected_before)
    after_hash = coords_hash(protected_after)
    if len(protected_before) != len(protected_after) or before_hash != after_hash:
        raise RuntimeError("Protected wrist/hand endpoint coordinates changed")
    return body, {"count": len(protected_before), "before": before_hash, "after": after_hash, "tolerance_m": 1e-6}


def make_curve(name: str, points: list[tuple[float, float, float]], depth: float, material: bpy.types.Material) -> bpy.types.Object:
    curve = bpy.data.curves.new(name + "_DATA", "CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth = depth
    curve.bevel_resolution = 3
    spline = curve.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for point, coordinate in zip(spline.points, points):
        point.co = (*coordinate, 1.0)
    obj = bpy.data.objects.new(name, curve)
    bpy.context.scene.collection.objects.link(obj)
    curve.materials.append(material)
    return obj


def add_box(
    name: str,
    location: tuple[float, float, float],
    scale: tuple[float, float, float],
    material: bpy.types.Material,
    bevel_width: float = 0.004,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    activate(obj)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    bevel = obj.modifiers.new(name + " Soft Edge", "BEVEL")
    bevel.width = bevel_width
    bevel.segments = 3
    activate(obj)
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    smooth(obj)
    return obj


def add_sock(name: str, x: float, material: bpy.types.Material) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=1.0, depth=0.12, location=(x, -0.010, 0.292))
    obj = bpy.context.object
    obj.name = name
    obj.scale = (0.050, 0.043, 1.0)
    activate(obj)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    smooth(obj)
    return obj


def build_wardrobe() -> tuple[list[bpy.types.Object], dict[str, object]]:
    created: list[bpy.types.Object] = []
    body, endpoint_audit = build_body()
    created.append(body)

    jacket = clone("V193_SCULPTED_OPEN_JACKET", "V195_JACKET")
    for vertex in jacket.data.vertices:
        if 1.03 < vertex.co.z < 1.51 and abs(vertex.co.x) < 0.235:
            vertex.co.x *= 0.965
            if vertex.co.y < -0.03:
                vertex.co.y += 0.003
    jacket.data.update()
    smooth(jacket)
    created.append(jacket)

    shirt = clone("V193_CONTOURED_FLORAL_SHIRT", "V195_SHIRT")
    for vertex in shirt.data.vertices:
        if 1.10 < vertex.co.z < 1.46 and vertex.co.y < -0.04:
            falloff = max(0.0, 1.0 - (abs(vertex.co.x) / 0.15) ** 2)
            vertex.co.y -= 0.0035 * falloff
    shirt.data.update()
    smooth(shirt)
    created.append(shirt)

    trousers = clone("V148_CLEAN_TRUE_BLACK_TROUSERS", "V195_TROUSERS")
    for vertex in trousers.data.vertices:
        center = 0.13 if vertex.co.x >= 0.0 else -0.13
        if 0.25 < vertex.co.z < 0.96:
            vertex.co.x = center + (vertex.co.x - center) * 0.96
    trousers.data.update()
    smooth(trousers)
    created.append(trousers)

    cuffs = clone("V89_CONNECTED_ROLLED_CUFFS", "V195_TROUSER_CUFFS")
    boot_l = clone("V90_CHELSEA_BOOT_ANATOMICAL_LEFT", "V195_BOOT_L")
    boot_r = clone("V90_CHELSEA_BOOT_ANATOMICAL_RIGHT", "V195_BOOT_R")
    created.extend([cuffs, boot_l, boot_r])
    sock_material = bpy.data.materials.get("V89_TRUE_BLACK_TROUSERS") or trousers.material_slots[0].material
    sock_l = add_sock("V195_SOCK_L", 0.213, sock_material)
    sock_r = add_sock("V195_SOCK_R", -0.213, sock_material)
    created.extend([sock_l, sock_r])

    jacket_material = jacket.material_slots[0].material
    shirt_material = shirt.material_slots[0].material
    thread_material = bpy.data.materials.get("V123_DARK_TAILORING_THREAD") or jacket_material
    boot_material = boot_l.material_slots[0].material
    for suffix, x in (("L", 0.145), ("R", -0.145)):
        pocket = add_box(f"V195_CHEST_POCKET_{suffix}", (x, -0.147, 1.332), (0.034, 0.004, 0.046), jacket_material, 0.003)
        flap = add_box(f"V195_CHEST_POCKET_FLAP_{suffix}", (x, -0.153, 1.382), (0.036, 0.003, 0.009), jacket_material, 0.002)
        seam = make_curve(
            f"V195_CHEST_POCKET_SEAM_{suffix}",
            [(x - 0.031, -0.157, 1.375), (x - 0.031, -0.157, 1.292), (x + 0.031, -0.157, 1.292), (x + 0.031, -0.157, 1.375)],
            0.0008,
            thread_material,
        )
        created.extend([pocket, flap, seam])

    pen = clone("V123_CONFORMING_POCKET_PEN", "V195_PEN")
    pen_clip = clone("V123_POCKET_PEN_CLIP", "V195_PEN_CLIP")
    created.extend([pen, pen_clip])

    collar = clone("V193_ROLLED_OPEN_JACKET_COLLAR", "V195_JACKET_COLLAR")
    shirt_collar = clone("V121_FLORAL_SHIRT_COLLAR", "V195_SHIRT_COLLAR")
    collar_stand = clone("V133_SEATED_SHIRT_COLLAR_STAND", "V195_SHIRT_COLLAR_STAND")
    collar_button = clone("V121_COLLAR_BUTTON", "V195_SHIRT_COLLAR_BUTTON")
    cuff_l = clone("V143_L_POSE_SPACE_CUFF", "V195_CUFF_L")
    cuff_r = clone("V193_TAILORED_PICKING_CUFF", "V195_CUFF_R")
    created.extend([collar, shirt_collar, collar_stand, collar_button, cuff_l, cuff_r])
    existing_right_cuff = bpy.data.objects.get("V143_R_POSE_SPACE_CUFF")
    if existing_right_cuff:
        existing_right_cuff.hide_render = True
        existing_right_cuff.hide_viewport = True

    placket = add_box("V195_SHIRT_PLACKET", (0.0, -0.155, 1.235), (0.009, 0.0025, 0.230), shirt_material, 0.0015)
    created.append(placket)
    for index in range(1, 8):
        created.append(clone(f"V83_SHIRT_BUTTON_{index:02d}", f"V195_SHIRT_BUTTON_{index:02d}"))
    for index in range(1, 5):
        created.append(
            clone(
                f"V127_ANATOMICAL_RIGHT_JACKET_BUTTON_{index:02d}",
                f"V195_JACKET_BUTTON_R_{index:02d}",
            )
        )

    created.extend(
        [
            make_curve("V195_JACKET_HEM_SEAM", [(-0.19, -0.123, 1.035), (0.0, -0.145, 1.018), (0.19, -0.123, 1.035)], 0.0010, thread_material),
            make_curve("V195_JACKET_CENTER_SEAM_L", [(0.025, -0.158, 1.06), (0.045, -0.167, 1.30), (0.075, -0.145, 1.48)], 0.0009, thread_material),
            make_curve("V195_JACKET_CENTER_SEAM_R", [(-0.025, -0.158, 1.06), (-0.045, -0.167, 1.30), (-0.075, -0.145, 1.48)], 0.0009, thread_material),
            make_curve("V195_TROUSER_CREASE_L", [(0.13, -0.150, 0.34), (0.13, -0.161, 0.64), (0.13, -0.158, 0.94)], 0.0008, thread_material),
            make_curve("V195_TROUSER_CREASE_R", [(-0.13, -0.150, 0.34), (-0.13, -0.161, 0.64), (-0.13, -0.158, 0.94)], 0.0008, thread_material),
        ]
    )

    for suffix, x, side in (("L", 0.213, 1.0), ("R", -0.213, -1.0)):
        sole = add_box(f"V195_BOOT_SOLE_{suffix}", (x, -0.080, 0.020), (0.068, 0.156, 0.012), boot_material, 0.004)
        elastic = add_box(f"V195_BOOT_ELASTIC_{suffix}", (x + side * 0.061, -0.030, 0.165), (0.003, 0.050, 0.050), sock_material, 0.004)
        tab = make_curve(f"V195_BOOT_PULL_TAB_{suffix}", [(x, 0.050, 0.245), (x, 0.054, 0.286)], 0.004, boot_material)
        created.extend([sole, elastic, tab])
    return created, endpoint_audit


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
    protected_before = snapshot_objects(excluded=TARGETS, excluded_prefixes=("V195_",))
    created, endpoint_audit = build_wardrobe()
    protected_after = snapshot_objects(excluded=TARGETS, excluded_prefixes=("V195_",))
    if protected_before != protected_after:
        raise RuntimeError(f"Protected scene changed: {protected_before} != {protected_after}")

    scene = bpy.context.scene
    scene["checkpoint"] = "V195"
    scene["checkpoint_intent"] = "finished body silhouette and reference-locked wardrobe"
    scene["source_checkpoint"] = source.name
    bpy.ops.wm.save_as_mainfile(filepath=str(output), check_existing=False)

    production = stage_root / "production_v195_wardrobe"
    orbit_dir = production / "renders" / "eight_angle"
    detail_dir = production / "renders" / "details"
    orbit = render_group(output, orbit_dir, BODY_CAMERAS, (600, 720))
    detail_cameras = {
        "torso_front": "V114_CAM_TORSO_FRONT",
        "front": BODY_CAMERAS["front"],
        "left_profile": BODY_CAMERAS["left_profile"],
        "back": BODY_CAMERAS["back"],
    }
    details = render_group(output, detail_dir, detail_cameras, (720, 720))
    render_manifest = {}
    for group, outputs, cameras in (("orbit", orbit, BODY_CAMERAS), ("details", details, detail_cameras)):
        render_manifest[group] = {
            label: {"camera": cameras[label], "path": str(Path(path).relative_to(stage_root)), "sha256": sha256(Path(path))}
            for label, path in outputs.items()
        }
    audit_path = production / "audit" / "v195_wardrobe_audit.json"
    write_json(
        audit_path,
        {
            "schema": "v195-wardrobe-audit",
            "source": str(source),
            "output": str(output),
            "source_sha256": sha256(source),
            "output_sha256": sha256(output),
            "runtime": bpy.app.version_string,
            "created": sorted({obj.name for obj in created}),
            "hidden_predecessors": sorted(TARGETS),
            "protected_before": protected_before,
            "protected_after": protected_after,
            "protected_identical": protected_before == protected_after,
            "endpoint_lock": endpoint_audit,
            "reference_locks": {
                "shirt": "fully_buttoned dark floral with seven visible buttons",
                "jacket": "charcoal work jacket with two chest pockets",
                "pen": "anatomical-left chest pocket",
                "trousers": "true black with rolled cuffs",
                "boots": "paired brown Chelsea boots",
            },
            "renders": render_manifest,
            "delivery": {"status": "pending host-Python contact-sheet composition"},
        },
    )
    write_json(production / "renders" / "v195_render_manifest.json", {"schema": "v195-render-manifest-v1", "renders": render_manifest})
    status = production / "HEADLESS_BUILD_STATUS_V195.md"
    status.parent.mkdir(parents=True, exist_ok=True)
    status.write_text(
        "# Character Asset_An — V195 Wardrobe\n\n"
        "V195 finishes the reference-locked work jacket, fully buttoned floral shirt, tapered black trousers with rolled cuffs, socks, and paired Chelsea boots while preserving the performance endpoints.\n\n"
        f"- Source SHA-256: `{sha256(source)}`\n"
        f"- Output SHA-256: `{sha256(output)}`\n"
        f"- Protected fingerprint: `{protected_before['sha256']}` before and after\n"
        f"- Protected endpoint vertices: `{endpoint_audit['count']}` unchanged\n"
        "- Structural and reopen validation: pending\n",
        encoding="utf-8",
    )
    print("V195_OUTPUT=" + str(output))


if __name__ == "__main__":
    main()
