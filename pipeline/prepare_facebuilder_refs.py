from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "references/facial/head_expression_sheet_v2_face_refined.png"
OUTPUT = ROOT / "production_v212_identity/facebuilder_refs"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


OUTPUT.mkdir(parents=True, exist_ok=True)
image = Image.open(SOURCE).convert("RGB")
if image.size != (1536, 1024):
    raise RuntimeError(f"Unexpected authoritative sheet size: {image.size}")

# The supplied sheet is an exact 3 x 2 layout. FaceBuilder receives only the
# neutral top-row views so expression changes cannot bias landmark fitting.
crops = {
    "facebuilder_front_neutral.png": (0, 0, 512, 512),
    "facebuilder_left_3q_neutral.png": (512, 0, 1024, 512),
    "facebuilder_left_profile_neutral.png": (1024, 0, 1536, 512),
}
records = {}
for name, box in crops.items():
    path = OUTPUT / name
    image.crop(box).save(path, optimize=True)
    records[name] = {"crop_box": list(box), "sha256": sha256(path), "size": [512, 512]}

manifest = {
    "schema": "character-an-facebuilder-reference-plate-v1",
    "authority": "supplied facial sheet",
    "source": str(SOURCE.relative_to(ROOT)),
    "source_sha256": sha256(SOURCE),
    "neutral_views": records,
    "fit_order": [
        "facebuilder_front_neutral.png",
        "facebuilder_left_profile_neutral.png",
        "facebuilder_left_3q_neutral.png",
    ],
    "note": "No generated imagery and no lower-row expression views are used for geometry fitting.",
}
(OUTPUT / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(manifest, indent=2, sort_keys=True))
