from __future__ import annotations

import sys
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.build_v207_playable_hands import OUTPUT, STAGE, render_acceptance
from pipeline.common import sha256, write_json


if Path(bpy.data.filepath).resolve() != OUTPUT.resolve():
    bpy.ops.wm.open_mainfile(filepath=str(OUTPUT))
root = bpy.data.objects["V206_GUITAR_ROOT"]
cameras = {
    "fretboard_overhead": "V207_CAM_OVERHEAD",
    "dorsal_oblique": "V207_CAM_DORSAL",
    "neck_edge": "V207_CAM_NECK_EDGE",
    "thumb_rear": "V207_CAM_THUMB_REAR",
    "contact_macro": "V207_CAM_CONTACT_MACRO",
    "wrist_context": "V207_CAM_WRIST",
}
manifest = render_acceptance(root, cameras)
output_hash = sha256(OUTPUT)
write_json(
    STAGE / "audit" / "v207_build_receipt.json",
    {
        "status": "PASS",
        "source": {
            "path": "production_v206_guitar/ant_headless_guitar_v206.blend",
            "sha256": "2529d85a667bb0f9f49a8f09473217d3871db5d2c175ed3839851b20bc0a86ef",
        },
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": output_hash},
        "hand_audit_sha256": sha256(STAGE / "audit" / "v207_hand_contact_audit.json"),
        "render_manifest_sha256": sha256(STAGE / "audit" / "v207_render_manifest.json"),
    },
)
print(f"V207_RENDER_RESUME_OK output_sha256={output_hash} renders={len(manifest['renders'])}")
