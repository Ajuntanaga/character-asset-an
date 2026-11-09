from __future__ import annotations

import json
import random
from pathlib import Path

import bpy
from mathutils import Vector

from pipeline import build_v204_groom as build
from pipeline.common import sha256, write_json


ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "production_v204_groom"
OUTPUT = STAGE / "ant_groomed_character_v204.blend"


def tune_material(name: str, color: tuple[float, float, float, float], roughness: float) -> None:
    material = bpy.data.materials[name]
    node = material.node_tree.nodes.get(f"{name}_FIBER_PRINCIPLED")
    build.require(node is not None, f"Missing fiber shader: {name}")
    node.inputs["Base Color"].default_value = color
    node.inputs["Roughness"].default_value = roughness
    node.inputs["Specular IOR Level"].default_value = 0.20
    node.inputs["Anisotropic"].default_value = 0.44
    node.inputs["Coat Weight"].default_value = 0.0
    material.diffuse_color = color


def main() -> None:
    scene = bpy.context.scene
    build.require(scene.get("checkpoint") == "V204_GROOM", "Photoreal repair requires V204 open")
    build.require(Path(bpy.data.filepath).resolve() == OUTPUT.resolve(), "Photoreal repair must target canonical V204")

    tune_material("MAT_V204_HAIR", (0.0025, 0.0018, 0.0012, 1.0), 0.52)
    tune_material("MAT_V204_HAIR_HIGHLIGHT", (0.006, 0.0035, 0.002, 1.0), 0.48)
    tune_material("MAT_V204_FACIAL_HAIR", (0.0035, 0.0023, 0.0015, 1.0), 0.54)

    bevels = {
        "V204_HAIR_GUIDES": 0.000055,
        "V204_HAIR_CHILDREN_DENSE": 0.000045,
        "V204_HAIR_CHILDREN_CLUMP": 0.000055,
        "V204_HAIR_CHILDREN_FRIZZ": 0.000028,
        "V204_HAIR_FLYAWAYS": 0.000022,
        "V204_BEARD_GUIDES": 0.000050,
        "V204_BEARD_CHILDREN": 0.000035,
        "V204_MUSTACHE_L": 0.000045,
        "V204_MUSTACHE_R": 0.000045,
        "V204_BROWS": 0.000045,
        "V204_LASHES": 0.000024,
    }
    for name, bevel in bevels.items():
        bpy.data.objects[name].data.bevel_depth = bevel
        bpy.data.objects[name].data.bevel_resolution = 2

    collection = bpy.data.collections["V204_GROOM_SYSTEMS"]
    old = bpy.data.objects.get("V204_HAIR_UNDERCOAT")
    if old is not None:
        bpy.data.objects.remove(old, do_unlink=True)
    body = bpy.data.objects["V202_BODY"]
    surface = build.Surface(body)
    rng = random.Random(build.SEEDS["scalp_undercoat"])
    strands = []
    for root, normal, phase in build.scalp_roots(surface, 7000, build.SEEDS["scalp_undercoat"]):
        side = -1.0 if root.x < build.PART_X else 1.0
        lean = Vector((side * rng.uniform(0.0006, 0.0020), rng.uniform(-0.0008, 0.0003), -rng.uniform(0.0, 0.0012)))
        strands.append(build.curl_strand(root, normal, rng.uniform(0.0075, 0.0115), rng.uniform(0.0006, 0.0010), phase, rng.uniform(0.46, 0.76), lean, 6))
    undercoat = build.make_curve_object(
        "V204_HAIR_UNDERCOAT", strands, 0.000040,
        bpy.data.materials["MAT_V204_HAIR"], collection, 7000,
    )
    build.attach_density(undercoat, bpy.data.node_groups["V204_GN_DENSITY_SCALP"])

    required_names = {
        "V204_HAIR_UNDERCOAT", "V204_HAIR_GUIDES", "V204_HAIR_CHILDREN_DENSE",
        "V204_HAIR_CHILDREN_CLUMP", "V204_HAIR_CHILDREN_FRIZZ", "V204_HAIR_FLYAWAYS",
        "V204_BEARD_GUIDES", "V204_BEARD_CHILDREN", "V204_MUSTACHE_L", "V204_MUSTACHE_R",
        "V204_BROWS", "V204_LASHES",
    }
    root_count = sum(len(bpy.data.objects[name].data.splines) for name in required_names)
    scene["v204_groom_layers"] = "undercoat,guides,dense_children,clump,frizz,flyaway,beard,mustache,brows,lashes"
    scene["v204_photoreal_groom_revision"] = "human_scale_fibers_dense_short_undercoat"

    audit_path = STAGE / "audit" / "v204_groom_audit.json"
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    audit["root_count"] = root_count
    audit["curve_systems"] = {name: len(bpy.data.objects[name].data.splines) for name in sorted(required_names)}
    audit["fiber_radius_m"] = {name: bpy.data.objects[name].data.bevel_depth for name in sorted(required_names)}
    audit["photoreal_revision"] = "human_scale_fibers_dense_short_undercoat"
    write_json(audit_path, audit)

    cameras = {name: bpy.data.objects[name] for name in build.REQUIRED_CAMERAS} if hasattr(build, "REQUIRED_CAMERAS") else {
        name: bpy.data.objects[name] for name in (
            "V204_CAM_FRONT", "V204_CAM_PROFILE", "V204_CAM_REAR",
            "V204_CAM_TOP", "V204_CAM_RIM", "V204_CAM_ROOT_MACRO",
        )
    }
    render_results = build.render_suite(cameras)
    manifest_path = STAGE / "audit" / "v204_render_manifest.json"
    write_json(manifest_path, {
        "schema": "v204-render-manifest-v1",
        "checkpoint": "V204_GROOM",
        "renderer": "Cycles CPU",
        "adaptive_sampling": True,
        "renders": render_results,
    })

    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), compress=True)
    output_hash = sha256(OUTPUT)
    receipt_path = STAGE / "audit" / "v204_build_receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["output"] = {"path": str(OUTPUT.relative_to(ROOT)), "sha256": output_hash, "bytes": OUTPUT.stat().st_size}
    receipt["groom_audit"] = {"path": str(audit_path.relative_to(ROOT)), "sha256": sha256(audit_path)}
    receipt["render_manifest"] = {"path": str(manifest_path.relative_to(ROOT)), "sha256": sha256(manifest_path)}
    receipt["curve_systems"] = len(required_names)
    receipt["root_count"] = root_count
    receipt["photoreal_revision"] = scene["v204_photoreal_groom_revision"]
    write_json(receipt_path, receipt)
    print(f"V204_PHOTOREAL_GROOM_OK sha256={output_hash} roots={root_count} renders={len(render_results)}")


if __name__ == "__main__":
    main()
