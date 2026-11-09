"""Extract a directly reviewable guitar-body contour from the product photo."""

from pathlib import Path
import json
import sys


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
VISION = ROOT / ".vision_packages"
if str(VISION) not in sys.path:
    sys.path.insert(0, str(VISION))

import cv2
import numpy as np


SOURCE = ROOT / "references" / "props" / "strandberg" / "strandberg_full_product.jpg"
STAGE = ROOT / "production_v318_reference_guitar_rebuild"
ANALYSIS = STAGE / "analysis"
OUTPUT_JSON = ANALYSIS / "strandberg_cv_silhouette.json"
OUTPUT_OVERLAY = ANALYSIS / "strandberg_cv_silhouette_overlay.png"

# Calibrated from the supplied front photograph and the established V206 scale.
PHOTO_CENTER_X_PX = 727.0
LOCAL_Y_M_PER_PX = 0.000342
PHOTO_BODY_TOP_Y_PX = 180.0
PHOTO_BODY_BOTTOM_Y_PX = 1940.0
LOCAL_BODY_X_MIN_M = 0.360
LOCAL_BODY_X_MAX_M = 0.960
NECK_ERASE = (500, 0, 900, 805)


def local_point(pixel_x, pixel_y):
    fraction = (float(pixel_y) - PHOTO_BODY_TOP_Y_PX) / (PHOTO_BODY_BOTTOM_Y_PX - PHOTO_BODY_TOP_Y_PX)
    local_x = LOCAL_BODY_X_MIN_M + fraction * (LOCAL_BODY_X_MAX_M - LOCAL_BODY_X_MIN_M)
    local_y = (PHOTO_CENTER_X_PX - float(pixel_x)) * LOCAL_Y_M_PER_PX
    return [round(local_x, 8), round(local_y, 8)]


def main():
    ANALYSIS.mkdir(parents=True, exist_ok=True)
    image = cv2.imread(str(SOURCE), cv2.IMREAD_COLOR)
    if image is None:
        raise RuntimeError(f"Unable to read {SOURCE}")
    # The authoritative product image has a near-white background. Preserve
    # dark body pixels, then remove the connected neck/string corridor so the
    # remaining largest component closes at the real neck pocket.
    mask = np.any(image < 245, axis=2).astype(np.uint8) * 255
    x0, y0, x1, y1 = NECK_ERASE
    mask[y0:y1, x0:x1] = 0
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    contours, _hierarchy = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not contours:
        raise RuntimeError("No contour found in supplied product photo")
    contour = max(contours, key=cv2.contourArea)
    if cv2.contourArea(contour) < 300000:
        raise RuntimeError(f"Largest contour unexpectedly small: {cv2.contourArea(contour)}")
    silhouette = np.zeros(mask.shape, np.uint8)
    cv2.drawContours(silhouette, [contour], -1, 255, thickness=cv2.FILLED)
    contour, = cv2.findContours(silhouette, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0]
    perimeter = cv2.arcLength(contour, True)
    approximate = cv2.approxPolyDP(contour, epsilon=0.0026 * perimeter, closed=True)
    pixels = [[int(point[0][0]), int(point[0][1])] for point in approximate]
    points = [local_point(pixel_x, pixel_y) for pixel_x, pixel_y in pixels]

    overlay = image.copy()
    cv2.drawContours(overlay, [contour], -1, (40, 210, 40), 3)
    cv2.drawContours(overlay, [approximate], -1, (20, 30, 235), 3)
    for pixel_x, pixel_y in pixels:
        cv2.circle(overlay, (pixel_x, pixel_y), 5, (235, 80, 20), -1)
    cv2.rectangle(overlay, (x0, y0), (x1, y1), (255, 120, 30), 2)
    cv2.imwrite(str(OUTPUT_OVERLAY), overlay)

    record = {
        "schema": "strandberg-cv-silhouette-v1",
        "source": str(SOURCE.relative_to(ROOT)),
        "method": "white-background segmentation; neck corridor removal; largest filled component; bounded contour simplification",
        "source_resolution": [int(image.shape[1]), int(image.shape[0])],
        "neck_erase_px": list(NECK_ERASE),
        "contour_area_px2": float(cv2.contourArea(contour)),
        "contour_perimeter_px": float(perimeter),
        "approximation_points": len(points),
        "pixel_points": pixels,
        "points": points,
        "coordinate_mapping": {
            "photo_center_x_px": PHOTO_CENTER_X_PX,
            "local_y_m_per_px": LOCAL_Y_M_PER_PX,
            "photo_body_y_range_px": [PHOTO_BODY_TOP_Y_PX, PHOTO_BODY_BOTTOM_Y_PX],
            "local_body_x_range_m": [LOCAL_BODY_X_MIN_M, LOCAL_BODY_X_MAX_M],
        },
        "overlay": str(OUTPUT_OVERLAY.relative_to(ROOT)),
    }
    OUTPUT_JSON.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("V318_GUITAR_SILHOUETTE_OK=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
