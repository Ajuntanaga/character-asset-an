"""Extract the body silhouette from the supplied white-background product photo."""
from pathlib import Path
import json

import cv2
import numpy as np

ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "references/props/strandberg/strandberg_full_product.jpg"
OUTDIR = ROOT / "production_v340_image_contour_body" / "analysis"
JSON_OUT = OUTDIR / "strandberg_product_contour.json"
PREVIEW = OUTDIR / "strandberg_product_contour_preview.png"

image = cv2.imread(str(SOURCE), cv2.IMREAD_COLOR)
if image is None:
    raise RuntimeError(f"Unable to read {SOURCE}")

# The source has a clean white background. Preserve the dark instrument and
# explicitly remove the cropped neck above the body so the contour follows both
# inner horn cutaways instead of continuing off-frame.
distance = 255 - image.min(axis=2)
mask = np.where(distance > 13, 255, 0).astype(np.uint8)
h, w = mask.shape
mask[: int(h * 0.385), int(w * 0.355) : int(w * 0.565)] = 0
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)

contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
if not contours:
    raise RuntimeError("No contour found")
contour = max(contours, key=cv2.contourArea)
epsilon = 0.0032 * cv2.arcLength(contour, True)
approx = cv2.approxPolyDP(contour, epsilon, True).reshape(-1, 2)

preview = image.copy()
cv2.drawContours(preview, [approx.reshape(-1, 1, 2)], -1, (0, 0, 255), 6)
for index, (x, y) in enumerate(approx):
    cv2.circle(preview, (int(x), int(y)), 7, (255, 0, 0), -1)
    cv2.putText(preview, str(index), (int(x) + 8, int(y) - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 0, 0), 1, cv2.LINE_AA)

OUTDIR.mkdir(parents=True, exist_ok=True)
cv2.imwrite(str(PREVIEW), preview)
record = {
    "source": str(SOURCE.relative_to(ROOT)),
    "image_size": [w, h],
    "neck_erase": [int(w * 0.355), 0, int(w * 0.565), int(h * 0.385)],
    "area_px2": float(cv2.contourArea(contour)),
    "points_px": [[int(x), int(y)] for x, y in approx],
}
JSON_OUT.write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps({"points": len(approx), "preview": str(PREVIEW), "json": str(JSON_OUT)}))
