from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline import build_v206_guitar as build
from pipeline.common import sha256, write_json


STAGE = ROOT / "production_v206_guitar"
OUTPUT = STAGE / "ant_headless_guitar_v206.blend"


def main() -> None:
    build.require(bpy.context.scene.get("checkpoint") == "V206_GUITAR", "V206 must be open")
    figured = bpy.data.materials["MAT_V206_FIGURED_CHARCOAL"]
    ramp = next(node for node in figured.node_tree.nodes if node.bl_idname == "ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.0015, 0.0020, 0.0025, 1.0)
    ramp.color_ramp.elements[1].color = (0.028, 0.034, 0.038, 1.0)
    figured.diffuse_color = (0.012, 0.016, 0.019, 1.0)
    bpy.context.scene.view_settings.exposure = -1.8
    manifest = build.render_acceptance(bpy.data.objects["V206_GUITAR_ROOT"])
    bpy.context.scene["v206_material_revision"] = "smoky charcoal figured top; calibrated AgX exposure"
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), compress=True)
    output_hash = sha256(OUTPUT)
    receipt_path = STAGE / "audit" / "v206_build_receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["output"] = {"path": str(OUTPUT.relative_to(ROOT)), "sha256": output_hash, "bytes": OUTPUT.stat().st_size}
    receipt["material_revision"] = bpy.context.scene["v206_material_revision"]
    receipt["render_manifest_sha256"] = sha256(STAGE / "audit" / "v206_render_manifest.json")
    write_json(receipt_path, receipt)
    audit_path = STAGE / "audit" / "v206_guitar_audit.json"
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    audit["material_revision"] = bpy.context.scene["v206_material_revision"]
    audit["acceptance_render_count"] = len(manifest["renders"])
    write_json(audit_path, audit)
    print(f"V206_MATERIAL_REPAIR_OK sha256={output_hash} renders={len(manifest['renders'])}")


if __name__ == "__main__":
    main()
