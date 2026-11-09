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
    for name, energy in (("V206_KEY", 450.0), ("V206_FILL", 120.0), ("V206_RIM", 300.0)):
        bpy.data.objects[name].data.energy = energy
    manifest = build.render_acceptance(bpy.data.objects["V206_GUITAR_ROOT"])
    bpy.context.scene["v206_lighting_revision"] = "isolated V206 lights; inherited lights hidden; calibrated world"
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), compress=True)
    output_hash = sha256(OUTPUT)
    receipt_path = STAGE / "audit" / "v206_build_receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["output"] = {"path": str(OUTPUT.relative_to(ROOT)), "sha256": output_hash, "bytes": OUTPUT.stat().st_size}
    receipt["lighting_revision"] = bpy.context.scene["v206_lighting_revision"]
    receipt["render_manifest_sha256"] = sha256(STAGE / "audit" / "v206_render_manifest.json")
    write_json(receipt_path, receipt)
    audit_path = STAGE / "audit" / "v206_guitar_audit.json"
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    audit["lighting_revision"] = bpy.context.scene["v206_lighting_revision"]
    audit["acceptance_render_count"] = len(manifest["renders"])
    write_json(audit_path, audit)
    print(f"V206_LIGHTING_REPAIR_OK sha256={output_hash} renders={len(manifest['renders'])}")


if __name__ == "__main__":
    main()
