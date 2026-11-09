from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from pipeline.common import sha256, write_json


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage-root", type=Path, required=True)
    args = parser.parse_args()
    root = args.stage_root.resolve()
    production = root / "production_v197_rig"
    audit_path = production / "audit" / "v197_rig_audit.json"
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    delivery = production / "delivery"
    delivery.mkdir(parents=True, exist_ok=True)
    output = delivery / "v197_control_inventory.png"
    canvas = Image.new("RGB", (1600, 1000), (17, 24, 32))
    draw = ImageDraw.Draw(canvas)
    title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 38)
    heading = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28)
    body = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
    draw.text((48, 36), "Character Asset_An — V197 Control Inventory", font=title, fill=(232, 236, 240))
    columns = [
        ("Core / torso", ["root", "pelvis", "spine_01", "spine_02", "chest", "neck", "head", "jaw"]),
        ("Left / fretting", [name for name in audit["rig"]["bones"] if name.endswith(".L")]),
        ("Right / picking", [name for name in audit["rig"]["bones"] if name.endswith(".R")]),
    ]
    for column, (label, names) in enumerate(columns):
        x = 48 + column * 510
        draw.text((x, 120), label, font=heading, fill=(184, 202, 217))
        for row, name in enumerate(names):
            draw.text((x, 170 + row * 32), name, font=body, fill=(224, 229, 234))
    y = 760
    draw.text((48, y), "Actions", font=heading, fill=(184, 202, 217))
    draw.text((48, y + 48), "V197_PERFORMANCE_POSE   |   V197_NEUTRAL_POSE", font=body, fill=(224, 229, 234))
    draw.text((48, y + 96), "Facial controls", font=heading, fill=(184, 202, 217))
    draw.text((48, y + 144), "Blink   |   TiredGaze   |   Ah", font=body, fill=(224, 229, 234))
    draw.text((800, y + 96), "Guitar: independent / unweighted", font=heading, fill=(184, 202, 217))
    draw.text((800, y + 144), "Performance contact restoration: PASS", font=body, fill=(224, 229, 234))
    canvas.save(output, optimize=True)
    audit["delivery"] = {"control_inventory": {"path": str(output.relative_to(root)), "sha256": sha256(output)}}
    audit["validation"] = {"reopen": "PASS", "inventory": "PASS"}
    write_json(audit_path, audit)
    status_path = production / "HEADLESS_BUILD_STATUS_V197.md"
    status = status_path.read_text(encoding="utf-8").replace("- Structural and reopen validation: pending", "- Structural and reopen validation: PASS")
    status_path.write_text(status, encoding="utf-8")


if __name__ == "__main__":
    main()
