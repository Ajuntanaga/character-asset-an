#!/usr/bin/env python3
"""Extract a dense body silhouette from the supplied straight-on product photo."""

from pathlib import Path
import json

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "references" / "props" / "strandberg" / "strandberg_full_product.jpg"
OUT = ROOT / "production_v298_reference_guitar_body" / "analysis"
JSON_OUT = OUT / "strandberg_body_outline.json"
PREVIEW = OUT / "strandberg_body_outline_preview.png"


def main():
    image = Image.open(SOURCE).convert("RGB")

    # Clockwise reference landmarks in source pixels. The maple neck occludes
    # the neck pocket, so its two pocket corners are stated explicitly instead
    # of allowing a luminance trace to bridge across both cutaways.
    landmarks = [
        (530, 760), (480, 738), (430, 650), (360, 540), (275, 490),
        (205, 410), (155, 315), (135, 230), (165, 182),
        (135, 190), (118, 245), (126, 350), (175, 510), (240, 700),
        (274, 860), (268, 1000), (220, 1160), (150, 1320), (96, 1450),
        (82, 1540), (98, 1625), (150, 1720), (230, 1790), (330, 1814),
        (400, 1780), (448, 1690), (650, 1640), (805, 1620), (870, 1600),
        (905, 1598), (945, 1532), (1020, 1460), (1130, 1400),
        (1250, 1342), (1272, 1310), (1240, 1270), (1180, 1205),
        (1122, 1120), (1080, 1000), (1078, 900), (1118, 800),
        (1180, 700), (1172, 650), (1130, 620), (1080, 632),
        (1000, 680), (905, 704), (820, 700), (800, 760),
    ]

    def chaikin(points, passes=2):
        result = [(float(x), float(y)) for x, y in points]
        for _ in range(passes):
            refined = []
            for first, second in zip(result, result[1:] + result[:1]):
                refined.append((.75 * first[0] + .25 * second[0], .75 * first[1] + .25 * second[1]))
                refined.append((.25 * first[0] + .75 * second[0], .25 * first[1] + .75 * second[1]))
            result = refined
        return result

    traced = chaikin(landmarks, 2)

    # Product-photo pixels -> established V206 guitar local coordinates.
    # Local X runs nut-to-bridge; local Y spans the body.
    center_px = 727.0
    lateral_scale = 0.000342
    outline = [
        (
            0.360 + (pixel_y - 170.0) * ((0.960 - 0.360) / (1830.0 - 170.0)),
            (center_px - pixel_x) * lateral_scale,
        )
        for pixel_x, pixel_y in traced
    ]

    OUT.mkdir(parents=True, exist_ok=True)
    record = {
        "schema": "strandberg-product-outline-v1",
        "source": str(SOURCE.relative_to(ROOT)),
        "method": "manual product-photo landmarks plus two-pass Chaikin interpolation",
        "landmarks_px": landmarks,
        "coordinate_mapping": {
            "local_x_range_m": [0.360, 0.960],
            "image_center_x_px": center_px,
            "local_y_m_per_px": lateral_scale,
        },
        "points": outline,
    }
    JSON_OUT.write_text(json.dumps(record, indent=2) + "\n")

    preview = image.copy()
    draw = ImageDraw.Draw(preview)
    draw.line(traced + [traced[0]], fill=(255, 32, 32), width=5)
    preview.save(PREVIEW)
    print(json.dumps({"outline": str(JSON_OUT), "preview": str(PREVIEW), "points": len(outline)}))


if __name__ == "__main__":
    main()
