from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.common import sha256, write_json


STAGE = ROOT / "delivery_v210"
OUTPUT = STAGE / "Character_An_Performance_v210.blend"
VALIDATION = STAGE / "audit" / "v210_blender_validation.json"
MANIFEST = STAGE / "audit" / "v210_delivery_manifest.json"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def sheet(items: list[tuple[str, Path]], output: Path, title: str, columns: int = 3) -> Path:
    cell_w, cell_h, pad, title_h, label_h = 500, 650, 18, 72, 42
    rows = (len(items) + columns - 1) // columns
    canvas = Image.new("RGB", (columns * cell_w + (columns + 1) * pad, title_h + rows * (cell_h + label_h + pad) + pad), (17, 24, 32))
    draw = ImageDraw.Draw(canvas)
    draw.text((pad, 17), title, font=ImageFont.truetype(BOLD, 29), fill=(236, 240, 245))
    font = ImageFont.truetype(FONT, 19)
    for index, (label, path) in enumerate(items):
        with Image.open(path) as source:
            rendered = ImageOps.contain(source.convert("RGB"), (cell_w, cell_h), Image.Resampling.LANCZOS)
        col, row = index % columns, index // columns
        x, y = pad + col * (cell_w + pad), title_h + row * (cell_h + label_h + pad)
        draw.rounded_rectangle((x, y, x + cell_w, y + cell_h), radius=10, fill=(29, 38, 48))
        canvas.paste(rendered, (x + (cell_w - rendered.width) // 2, y + (cell_h - rendered.height) // 2))
        draw.text((x + 6, y + cell_h + 9), label, font=font, fill=(216, 226, 235))
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output, optimize=True)
    return output


def main() -> None:
    validation = json.loads(VALIDATION.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    output_hash = sha256(OUTPUT)
    if validation.get("status") != "PASS" or validation.get("validated_output_sha256") != output_hash:
        raise RuntimeError("V210 validation is absent or stale")
    if manifest.get("output", {}).get("sha256") != output_hash:
        raise RuntimeError("V210 manifest is stale")
    render_dir = ROOT / "production_v209_lookdev" / "renders" / "hero"
    delivery = STAGE / "images"
    contact = sheet(
        [(name.replace("_", " "), render_dir / f"{name}.png") for name in ("front", "three_quarter", "profile", "hero", "fretting_macro", "picking_macro")],
        delivery / "Character_An_v210_contact.png",
        "Character Asset_An V210 delivery",
    )
    comparison = sheet(
        [
            ("SUPPLIED character lock", ROOT / "references" / "source" / "approved_character_design_lock.png"),
            ("V210 front", render_dir / "front.png"),
            ("V210 hero", render_dir / "hero.png"),
            ("SUPPLIED hand target", ROOT / "references" / "hands" / "m3_chord_hand_v3_compact.png"),
            ("V210 fretting contact", render_dir / "fretting_macro.png"),
            ("V210 picking contact", render_dir / "picking_macro.png"),
        ],
        delivery / "Character_An_v210_reference_comparison.png",
        "V210 supplied-reference comparison and contact evidence",
    )
    readme = STAGE / "README.md"
    readme.write_text(
        "# Character Asset_An V210\n\n"
        f"- Blender asset: `Character_An_Performance_v210.blend`\n- SHA-256: `{output_hash}`\n"
        "- Blender: 5.2.2 LTS; Cycles / AgX.\n"
        "- Rig: `V208_PERFORMANCE_RIG` (16 bones).\n"
        "- Guitar: eight-string, 24-fret multiscale; straight F7 neutral.\n"
        "- Fretting contacts: index S5/F9, middle S4/F10, ring S7/F9, pinky S8/F11; pads sit 18% behind the wire with 1.85 mm string depression.\n"
        "- Visual boundary: physically based procedural/stylized hero asset; it is not a scan-grade digital human.\n",
        encoding="utf-8",
    )
    final = {
        "schema": "character-an-v210-final-audit-v1",
        "status": "PASS",
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": output_hash, "bytes": OUTPUT.stat().st_size},
        "validation": {"path": str(VALIDATION.relative_to(ROOT)), "sha256": sha256(VALIDATION)},
        "manifest": {"path": str(MANIFEST.relative_to(ROOT)), "sha256": sha256(MANIFEST)},
        "delivery_images": {str(path.relative_to(ROOT)): sha256(path) for path in (contact, comparison)},
        "readme": {"path": str(readme.relative_to(ROOT)), "sha256": sha256(readme)},
        "visual_boundary": validation.get("visual_boundary"),
    }
    audit = STAGE / "audit" / "v210_final_audit.json"
    write_json(audit, final)
    print(f"V210_FINALIZE_OK audit={audit.relative_to(ROOT)} sha256={sha256(audit)}")


if __name__ == "__main__":
    main()
