from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline import build_v205_wardrobe as build
from pipeline.common import sha256, write_json


STAGE = ROOT / "production_v205_wardrobe"
OUTPUT = STAGE / "ant_wardrobe_boots_v205.blend"


def shell(name: str, predicate, offset: float, material: bpy.types.Material, role: str) -> bpy.types.Object:
    body = bpy.data.objects["V202_BODY"]
    old = bpy.data.objects.get(name)
    if old is not None:
        bpy.data.objects.remove(old, do_unlink=True)
    selected = []
    used = set()
    for polygon in body.data.polygons:
        world = body.matrix_world @ polygon.center
        if predicate(world):
            selected.append(polygon)
            used.update(polygon.vertices)
    mapping = {old_index: new_index for new_index, old_index in enumerate(sorted(used))}
    vertices = []
    for index in sorted(used):
        vertex = body.data.vertices[index]
        vertices.append(tuple(vertex.co + vertex.normal * offset))
    faces = [tuple(mapping[index] for index in polygon.vertices) for polygon in selected]
    mesh = bpy.data.meshes.new(name + "_MESH")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.data.collections["V205_WARDROBE"].objects.link(obj)
    obj.matrix_world = body.matrix_world.copy()
    obj.data.materials.append(material)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    build.tag(obj, role)
    solidify = obj.modifiers.new("V205_FABRIC_THICKNESS", "SOLIDIFY")
    solidify.thickness = 0.0016 if "BOOT" not in name else 0.0030
    solidify.offset = 0.0
    obj["source_surface"] = "V202_BODY"
    obj["surface_offset_m"] = offset
    obj["face_count"] = len(faces)
    return obj


def hide(names: tuple[str, ...]) -> None:
    for name in names:
        obj = bpy.data.objects.get(name)
        if obj is not None:
            obj.hide_render = True
            obj.hide_viewport = True
            obj["blockout_replaced_by_fitted_shell"] = True


def main() -> None:
    build.require(bpy.context.scene.get("checkpoint") == "V205_WARDROBE_BOOTS", "V205 must be open")
    jacket = bpy.data.materials["MAT_V205_CHARCOAL_JACKET"]
    shirt = bpy.data.materials["MAT_V205_DARK_FLORAL_SHIRT"]
    trousers = bpy.data.materials["MAT_V205_TRUE_BLACK_TROUSERS"]
    leather = bpy.data.materials["MAT_V205_BROWN_BOOT_LEATHER"]

    fitted_shirt = shell(
        "V205_FITTED_SHIRT_SHELL",
        lambda p: 1.015 < p.z < 1.505 and abs(p.x) < 0.205,
        0.0045, shirt, "fitted dark floral shirt underlayer",
    )
    fitted_jacket = shell(
        "V205_FITTED_JACKET_SHELL",
        lambda p: 0.965 < p.z < 1.505 and not (p.y < -0.055 and abs(p.x) < 0.078 and p.z > 1.035),
        0.0120, jacket, "open fitted charcoal work jacket shell",
    )
    fitted_trousers = shell(
        "V205_FITTED_TROUSERS_SHELL",
        lambda p: 0.265 < p.z < 1.055 and abs(p.x) < (0.275 if p.z > 0.72 else 0.315),
        0.0080, trousers, "continuous fitted tapered trouser shell",
    )
    fitted_boot_l = shell(
        "V205_FITTED_BOOT_L",
        lambda p: p.z < 0.325 and p.x > 0.060,
        0.0110, leather, "fitted brown Chelsea boot upper left",
    )
    fitted_boot_r = shell(
        "V205_FITTED_BOOT_R",
        lambda p: p.z < 0.325 and p.x < -0.060,
        0.0110, leather, "fitted brown Chelsea boot upper right",
    )

    hide((
        "V205_SHIRT_BODY", "V205_JACKET_BODY", "V205_JACKET_SLEEVE_L", "V205_JACKET_SLEEVE_R",
        "V205_JACKET_CUFF_L", "V205_JACKET_CUFF_R", "V205_TROUSERS_HIP", "V205_TROUSER_LEG_L",
        "V205_TROUSER_LEG_R", "V205_TROUSERS_WAISTBAND", "V205_TROUSER_WAISTBAND",
        "V205_BOOT_L", "V205_BOOT_R", "V205_BOOT_SHAFT_L", "V205_BOOT_SHAFT_R",
    ))

    scene = bpy.context.scene
    scene["v205_visible_geometry_revision"] = "continuous body-derived fitted shells plus separate tailoring details"
    audit_path = STAGE / "audit" / "v205_wardrobe_audit.json"
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    audit["visible_geometry_revision"] = scene["v205_visible_geometry_revision"]
    audit["fitted_shells"] = {
        obj.name: {"faces": len(obj.data.polygons), "offset_m": obj["surface_offset_m"], "role": obj["wardrobe_role"]}
        for obj in (fitted_shirt, fitted_jacket, fitted_trousers, fitted_boot_l, fitted_boot_r)
    }
    audit["blockout_geometry"] = "retained hidden for construction provenance; excluded from acceptance renders"
    write_json(audit_path, audit)

    cameras = {name: bpy.data.objects[name] for name in (
        "V205_CAM_FRONT", "V205_CAM_THREE_QUARTER", "V205_CAM_PROFILE",
        "V205_CAM_REAR", "V205_CAM_TORSO", "V205_CAM_BOOTS",
    )}
    renders = build.render_suite(cameras)
    manifest_path = STAGE / "audit" / "v205_render_manifest.json"
    write_json(manifest_path, {"schema": "v205-render-manifest-v1", "checkpoint": "V205_WARDROBE_BOOTS", "renderer": "Cycles CPU", "renders": renders})
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), compress=True)
    output_hash = sha256(OUTPUT)
    receipt_path = STAGE / "audit" / "v205_build_receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["output"] = {"path": str(OUTPUT.relative_to(ROOT)), "sha256": output_hash, "bytes": OUTPUT.stat().st_size}
    receipt["wardrobe_audit"] = {"path": str(audit_path.relative_to(ROOT)), "sha256": sha256(audit_path)}
    receipt["render_manifest"] = {"path": str(manifest_path.relative_to(ROOT)), "sha256": sha256(manifest_path)}
    receipt["visible_geometry_revision"] = scene["v205_visible_geometry_revision"]
    write_json(receipt_path, receipt)
    print(f"V205_FITTED_SHELLS_OK sha256={output_hash} renders={len(renders)}")


if __name__ == "__main__":
    main()
