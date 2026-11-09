#!/usr/bin/env python3
"""Build a smooth production outline from the supplied Strandberg photograph.

All visible perimeter landmarks are measured from the front product photograph.
Only the lower center span hidden by the bridge/tuner assembly is inferred.
"""

from pathlib import Path
import json

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "references" / "props" / "strandberg" / "strandberg_full_product.jpg"
OUT = ROOT / "production_v318_reference_guitar_rebuild" / "analysis"
JSON_OUT = OUT / "strandberg_hybrid_outline.json"
PREVIEW = OUT / "strandberg_hybrid_outline_overlay.png"

# Clockwise, beginning at the bass-side neck pocket. Points outside the
# lower-center occlusion are taken from the corrected OpenCV perimeter.
LANDMARKS = [
    (500, 760), (499, 545), (415, 530), (325, 462), (250, 330),
    (179, 197), (151, 184), (139, 258), (137, 382), (205, 565),
    (277, 736), (304, 943), (273, 1076), (190, 1260), (101, 1435),
    (83, 1558), (110, 1680), (211, 1813), (288, 1901), (365, 1946),
    (410, 1961), (460, 1932), (486, 1896), (530, 1782),
    # Product body edge is hidden here by the headless tuner bank.
    (610, 1765), (705, 1738), (805, 1707), (875, 1690), (902, 1711),
    (909, 1653), (950, 1692), (969, 1725), (1009, 1733),
    (1156, 1575), (1320, 1508), (1390, 1478), (1409, 1440),
    (1325, 1335), (1231, 1225), (1183, 1100), (1188, 949),
    (1240, 810), (1285, 744), (1281, 687), (1223, 671),
    (1120, 720), (1019, 780), (900, 754),
]


def chaikin(points, passes=2):
    result = [(float(x), float(y)) for x, y in points]
    for _ in range(passes):
        refined = []
        for first, second in zip(result, result[1:] + result[:1]):
            refined.append((0.75 * first[0] + 0.25 * second[0], 0.75 * first[1] + 0.25 * second[1]))
            refined.append((0.25 * first[0] + 0.75 * second[0], 0.25 * first[1] + 0.75 * second[1]))
        result = refined
    return result


def local_point(pixel_x, pixel_y):
    # Official Boden 8 dimensions are 330 mm maximum width and 850 mm total
    # instrument length. The photographed saddle line is near y=1470 and maps
    # to the ~710 mm multiscale bridge, fixing the longitudinal calibration.
    local_x = 0.290 + float(pixel_y) * (0.560 / 1960.0)
    local_y = (727.0 - float(pixel_x)) * (0.330 / (1409.0 - 83.0))
    return [round(local_x, 8), round(local_y, 8)]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    traced = chaikin(LANDMARKS, 2)
    points = [local_point(x, y) for x, y in traced]
    # Corner cutting slightly contracts extrema. Restore the smoothed contour
    # to the manufacturer envelope without changing its measured silhouette.
    y_min = min(point[1] for point in points)
    y_max = max(point[1] for point in points)
    y_center = (y_min + y_max) * 0.5
    y_scale = 0.330 / (y_max - y_min)
    x_shift = 0.850 - max(point[0] for point in points)
    points = [
        [round(point[0] + x_shift, 8), round(y_center + (point[1] - y_center) * y_scale, 8)]
        for point in points
    ]
    record = {
        "schema": "strandberg-hybrid-outline-v1",
        "source": str(SOURCE.relative_to(ROOT)),
        "method": "measured visible photo perimeter plus smooth lower-center occlusion bridge; two-pass Chaikin refinement",
        "occluded_span_px": [[530, 1782], [902, 1711]],
        "landmarks_px": LANDMARKS,
        "coordinate_mapping": {
            "photo_center_x_px": 727.0,
            "local_y_m_per_px": 0.330 / (1409.0 - 83.0),
            "photo_body_y_range_px": [180.0, 1960.0],
            "local_body_x_range_m": [0.34142857, 0.85000000],
            "official_instrument_width_m": 0.330,
            "official_instrument_length_m": 0.850,
            "post_smoothing_y_scale": y_scale,
            "post_smoothing_x_shift_m": x_shift,
        },
        "points": points,
    }
    JSON_OUT.write_text(json.dumps(record, indent=2) + "\n")

    image = Image.open(SOURCE).convert("RGB")
    draw = ImageDraw.Draw(image)
    draw.line(traced + [traced[0]], fill=(255, 32, 32), width=5)
    for x, y in LANDMARKS:
        draw.ellipse((x - 4, y - 4, x + 4, y + 4), fill=(20, 100, 255))
    draw.line([(530, 1782), (610, 1765), (705, 1738), (805, 1707), (875, 1690), (902, 1711)], fill=(255, 170, 0), width=4)
    image.save(PREVIEW)
    print(json.dumps({"outline": str(JSON_OUT), "preview": str(PREVIEW), "points": len(points)}))


if __name__ == "__main__":
    main()
