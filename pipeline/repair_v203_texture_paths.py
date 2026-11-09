from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.common import sha256, write_json


STAGE = ROOT / "production_v203_skin_eyes"
OUTPUT = STAGE / "ant_skin_eyes_v203.blend"
RECEIPT = STAGE / "audit" / "v203_build_receipt.json"
MAP_KINDS = ("albedo", "roughness", "pore_normal", "fine_displacement_mask")


def main() -> None:
    if Path(bpy.data.filepath).resolve() != OUTPUT.resolve():
        raise RuntimeError(f"Open canonical V203 before repair: {OUTPUT}")
    for kind in MAP_KINDS:
        image = bpy.data.images.get(f"IMG_V203_{kind.upper()}")
        if image is None:
            raise RuntimeError(f"Missing V203 image datablock: {kind}")
        image.filepath = f"//textures/v203_skin_{kind}.<UDIM>.png"
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), compress=True)
    record = json.loads(RECEIPT.read_text(encoding="utf-8"))
    output_hash = sha256(OUTPUT)
    record["output"] = {
        "path": str(OUTPUT.relative_to(ROOT)),
        "sha256": output_hash,
        "bytes": OUTPUT.stat().st_size,
    }
    write_json(RECEIPT, record)
    print(f"V203_TEXTURE_PATHS_REPAIRED output_sha256={output_hash}")


if __name__ == "__main__":
    main()
