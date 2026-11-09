from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import bpy


STAGE_ROOT = Path(__file__).resolve().parents[1]
if str(STAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(STAGE_ROOT))

from pipeline.common import sha256, write_json
from pipeline.rendering import BODY_CAMERAS, HEAD_CAMERAS, render_group


def material_signature() -> str:
    records = []
    for obj in sorted(bpy.data.objects, key=lambda item: item.name):
        if obj.name.startswith("ANTV1_"):
            records.append((obj.name, [slot.material.name if slot.material else None for slot in obj.material_slots]))
    return json.dumps(records, separators=(",", ":"))


def principled_material(
    name: str,
    dark: tuple[float, float, float, float],
    light: tuple[float, float, float, float],
    roughness: float,
    noise_scale: float,
    bump_strength: float,
) -> bpy.types.Material:
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.use_nodes = True
    material.diffuse_color = light
    material["v199_roughness"] = roughness
    nodes = material.node_tree.nodes
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (520, 0)
    principled = nodes.new("ShaderNodeBsdfPrincipled")
    principled.name = "Principled BSDF"
    principled.location = (250, 0)
    principled.inputs["Roughness"].default_value = roughness
    if "Specular IOR Level" in principled.inputs:
        principled.inputs["Specular IOR Level"].default_value = 0.24
    texture = nodes.new("ShaderNodeTexCoord")
    texture.location = (-760, 20)
    noise = nodes.new("ShaderNodeTexNoise")
    noise.location = (-550, 20)
    noise.inputs["Scale"].default_value = noise_scale
    noise.inputs["Detail"].default_value = 4.5
    noise.inputs["Roughness"].default_value = 0.68
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.location = (-300, 40)
    ramp.color_ramp.elements[0].color = dark
    ramp.color_ramp.elements[1].color = light
    bump = nodes.new("ShaderNodeBump")
    bump.location = (0, -180)
    bump.inputs["Strength"].default_value = bump_strength
    bump.inputs["Distance"].default_value = 0.006
    links = material.node_tree.links
    links.new(texture.outputs["Generated"], noise.inputs["Vector"])
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], principled.inputs["Base Color"])
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], principled.inputs["Normal"])
    links.new(principled.outputs["BSDF"], output.inputs["Surface"])
    return material


def floral_material() -> bpy.types.Material:
    source = bpy.data.materials.get("V114_DESIGN_LOCK_FLORAL_MAT")
    if source and source.use_nodes:
        material = source.copy()
        material.name = "V199_SHIRT_MAT"
        material["v199_roughness"] = 0.70
        principled = material.node_tree.nodes.get("Principled BSDF")
        if principled:
            principled.inputs["Roughness"].default_value = 0.70
            base = principled.inputs["Base Color"]
            if base.is_linked:
                original = base.links[0]
                from_socket = original.from_socket
                material.node_tree.links.remove(original)
                hue = material.node_tree.nodes.new("ShaderNodeHueSaturation")
                hue.name = "V199 Dark Botanical Grade"
                hue.inputs["Saturation"].default_value = 0.70
                hue.inputs["Value"].default_value = 0.32
                material.node_tree.links.new(from_socket, hue.inputs["Color"])
                material.node_tree.links.new(hue.outputs["Color"], base)
            else:
                base.default_value = (0.028, 0.022, 0.015, 1.0)
        return material
    return principled_material(
        "V199_SHIRT_MAT",
        (0.008, 0.006, 0.004, 1.0),
        (0.13, 0.095, 0.050, 1.0),
        0.70,
        18.0,
        0.10,
    )


def line_material() -> bpy.types.Material:
    material = bpy.data.materials.get("V199_LINE_MAT") or bpy.data.materials.new("V199_LINE_MAT")
    material.use_nodes = True
    material.diffuse_color = (0.004, 0.003, 0.002, 1.0)
    nodes = material.node_tree.nodes
    principled = nodes.get("Principled BSDF")
    if principled:
        principled.inputs["Base Color"].default_value = (0.004, 0.003, 0.002, 1.0)
        principled.inputs["Roughness"].default_value = 0.92
    material["v199_roughness"] = 0.92
    return material


def assign(obj: bpy.types.Object, material: bpy.types.Material) -> None:
    if not obj.data or not hasattr(obj.data, "materials"):
        return
    obj.data.materials.clear()
    obj.data.materials.append(material)


def create_materials() -> dict[str, bpy.types.Material]:
    materials = {
        "skin": principled_material("V199_SKIN_MAT", (0.105, 0.027, 0.008, 1.0), (0.235, 0.080, 0.026, 1.0), 0.58, 5.0, 0.055),
        "hair": principled_material("V199_HAIR_MAT", (0.0002, 0.00015, 0.0001, 1.0), (0.008, 0.004, 0.002, 1.0), 0.88, 125.0, 0.32),
        "beard": principled_material("V199_BEARD_MAT", (0.004, 0.0015, 0.0007, 1.0), (0.040, 0.012, 0.004, 1.0), 0.84, 150.0, 0.20),
        "shirt": floral_material(),
        "jacket": principled_material("V199_JACKET_MAT", (0.005, 0.008, 0.011, 1.0), (0.031, 0.040, 0.048, 1.0), 0.76, 72.0, 0.14),
        "trousers": principled_material("V199_TROUSERS_MAT", (0.0012, 0.0015, 0.0018, 1.0), (0.010, 0.012, 0.014, 1.0), 0.80, 42.0, 0.08),
        "sock": principled_material("V199_SOCK_MAT", (0.0007, 0.0008, 0.0010, 1.0), (0.006, 0.007, 0.009, 1.0), 0.86, 85.0, 0.12),
        "boot": principled_material("V199_BOOT_MAT", (0.030, 0.007, 0.002, 1.0), (0.145, 0.044, 0.012, 1.0), 0.50, 7.0, 0.16),
        "line": line_material(),
        "lip": principled_material("V199_LIP_MAT", (0.055, 0.009, 0.006, 1.0), (0.16, 0.040, 0.022, 1.0), 0.54, 7.0, 0.03),
    }
    return materials


def assign_materials(materials: dict[str, bpy.types.Material]) -> dict[str, list[str]]:
    assigned: dict[str, list[str]] = {key: [] for key in materials}
    for obj in bpy.context.scene.objects:
        if obj.hide_render or obj.type not in {"MESH", "CURVE"}:
            continue
        name = obj.name
        upper = name.upper()
        target = None
        if name == "V195_BODY" or upper.startswith("V198_DEFORM_") or upper.startswith("V196_") and not any(token in upper for token in ("NAIL", "CREASE")):
            target = "skin"
        if upper.startswith("V194_"):
            if "HAIR" in upper:
                target = "hair"
            elif any(token in upper for token in ("BEARD", "MUSTACHE", "SOUL_PATCH")):
                target = "beard"
            elif any(token in upper for token in ("BROW", "NOSTRIL", "MOUTH_LINE")):
                target = "line"
            elif "MOUTH" in upper:
                target = "lip"
            elif any(token in upper for token in ("EYE_", "IRIS", "PUPIL")):
                target = None
            else:
                target = "skin"
        if upper.startswith("V195_JACKET") or upper.startswith("V195_CHEST_POCKET") or upper.startswith("V195_CUFF_"):
            target = "jacket"
        elif upper.startswith("V195_SHIRT") and "BUTTON" not in upper:
            target = "shirt"
        elif upper in {"V195_TROUSERS", "V195_TROUSER_CUFFS"} or "TROUSER_CREASE" in upper:
            target = "trousers"
        elif upper.startswith("V195_SOCK") or "BOOT_ELASTIC" in upper:
            target = "sock"
        elif upper.startswith("V195_BOOT"):
            target = "boot"
        elif any(token in upper for token in ("SEAM", "CREASE")) and upper.startswith("V195_"):
            target = "line"
        if "NAIL" in upper and upper.startswith("V196_"):
            target = "lip"
        if target:
            assign(obj, materials[target])
            assigned[target].append(name)
    return assigned


def configure_freestyle(scene: bpy.types.Scene) -> dict[str, object]:
    scene.render.use_freestyle = True
    view_layer = scene.view_layers[0]
    settings = view_layer.freestyle_settings
    if settings.linesets:
        lineset = settings.linesets[0]
    else:
        lineset = settings.linesets.new("V199 Travelling Contours")
    lineset.name = "V199 Travelling Contours"
    lineset.select_silhouette = True
    lineset.select_border = True
    lineset.select_contour = True
    lineset.select_external_contour = True
    lineset.select_crease = False
    lineset.select_material_boundary = False
    lineset.select_edge_mark = False
    lineset.visibility = "VISIBLE"
    style = lineset.linestyle
    style.name = "V199 Selective Ink"
    style.color = (0.012, 0.008, 0.005)
    style.thickness = 0.62
    style.alpha = 0.72
    style.use_chaining = True
    return {"engine": "Freestyle", "line_set": lineset.name, "line_style": style.name, "thickness_px": style.thickness, "travels_with_camera": True}


def missing_v199_textures(materials: dict[str, bpy.types.Material]) -> list[str]:
    missing = []
    for material in materials.values():
        if not material.use_nodes:
            continue
        for node in material.node_tree.nodes:
            image = getattr(node, "image", None)
            if image and image.source == "FILE" and image.packed_file is None:
                path = Path(bpy.path.abspath(image.filepath))
                if not path.is_file():
                    missing.append(f"{material.name}:{image.name}:{path}")
    return missing


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
    guitar_before = material_signature()
    materials = create_materials()
    assigned = assign_materials(materials)
    contour = configure_freestyle(bpy.context.scene)
    missing = missing_v199_textures(materials)
    if missing:
        raise RuntimeError("Missing V199 textures: " + ", ".join(missing))
    guitar_after = material_signature()
    if guitar_before != guitar_after:
        raise RuntimeError("Guitar material assignments changed")

    scene = bpy.context.scene
    scene["checkpoint"] = "V199"
    scene["checkpoint_intent"] = "reference-locked painterly materials and travelling contours"
    scene["source_checkpoint"] = source.name
    scene["v199_guitar_materials_before"] = guitar_before
    scene["v199_guitar_materials_after"] = guitar_after
    scene["v199_missing_external_textures"] = len(missing)
    scene["v199_contour_system"] = contour["line_set"]
    bpy.ops.wm.save_as_mainfile(filepath=str(output), check_existing=False)

    production = stage_root / "production_v199_lookdev"
    head_dir = production / "renders" / "head"
    orbit_dir = production / "renders" / "eight_angle"
    detail_dir = production / "renders" / "materials"
    heads = render_group(output, head_dir, HEAD_CAMERAS, (600, 600))
    orbit = render_group(output, orbit_dir, BODY_CAMERAS, (600, 720))
    detail_cameras = {
        "torso_front": "V114_CAM_TORSO_FRONT",
        "lower_detail": "V89_CAM_LOWER_DETAIL",
        "fretting_hand": "V142_FRETTING_CAMERA",
        "picking_hand": "V166_PICKING_OBLIQUE_CAMERA",
    }
    details = render_group(output, detail_dir, detail_cameras, (720, 720))
    manifests = {}
    for group, outputs, cameras in (("head", heads, HEAD_CAMERAS), ("orbit", orbit, BODY_CAMERAS), ("materials", details, detail_cameras)):
        manifests[group] = {
            label: {"camera": cameras[label], "path": str(Path(path).relative_to(stage_root)), "sha256": sha256(Path(path))}
            for label, path in outputs.items()
        }
    audit_path = production / "audit" / "v199_lookdev_audit.json"
    write_json(
        audit_path,
        {
            "schema": "v199-lookdev-audit",
            "source": str(source),
            "output": str(output),
            "source_sha256": sha256(source),
            "output_sha256": sha256(output),
            "runtime": bpy.app.version_string,
            "materials": {key: {"name": material.name, "roughness": material.get("v199_roughness")} for key, material in materials.items()},
            "assignments": assigned,
            "contour": contour,
            "guitar_materials_unchanged": guitar_before == guitar_after,
            "missing_external_textures": missing,
            "renders": manifests,
            "delivery": {"status": "pending host-Python contact-sheet composition"},
            "visual_review": "pending",
        },
    )
    status = production / "HEADLESS_BUILD_STATUS_V199.md"
    status.parent.mkdir(parents=True, exist_ok=True)
    status.write_text(
        "# Character Asset_An — V199 Look Development\n\n"
        "V199 applies procedural/local painterly materials to skin, curls, beard, floral shirt, work jacket, trousers, socks, and Chelsea boots, plus a visible-only camera-travelling contour system. Guitar materials remain unchanged.\n\n"
        "- External texture dependencies: `0 missing`\n"
        "- Guitar material assignments: unchanged\n"
        "- Structural/reopen validation: pending\n",
        encoding="utf-8",
    )
    print("V199_OUTPUT=" + str(output))


if __name__ == "__main__":
    main()
