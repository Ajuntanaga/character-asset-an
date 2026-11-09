"""Split the generated photoreal identity triptych into FaceBuilder views."""

from pathlib import Path

from PIL import Image


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "references/derived/photoreal_facebuilder_v1/character_an_photoreal_triptych_v1.png"
OUTPUT_DIR = SOURCE.parent


with Image.open(SOURCE) as image:
    width, height = image.size
    if width < 1800 or height != 813:
        raise RuntimeError(f"Unexpected triptych size: {(width, height)}")
    boundaries = (0, round(width / 3), round(2 * width / 3), width)
    for index, name in enumerate(("front", "three_quarter", "profile")):
        left, right = boundaries[index:index + 2]
        panel = image.crop((left, 0, right, height))
        panel.save(OUTPUT_DIR / f"character_an_{name}_v1.png")

print("FACEBUILDER_TRIPTYCH_SPLIT_OK")
