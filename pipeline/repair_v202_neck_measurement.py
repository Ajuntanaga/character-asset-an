from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline import build_v202_neutral_anatomy as v202_builder
from pipeline.common import write_json


v202_builder = importlib.reload(v202_builder)

OUTPUT = ROOT / "production_v202_neutral_anatomy" / "ant_neutral_anatomy_v202.blend"
MEASUREMENTS = ROOT / "production_v202_neutral_anatomy" / "analysis" / "v202_landmark_measurements.json"
REJECTED_PRE_REVIEW = (
    ROOT
    / "production_v202_neutral_anatomy"
    / "audit"
    / "v202_rejected_square_jaw_coin_nails.blend"
)


def main() -> None:
    v202_builder.require(Path(bpy.data.filepath).resolve() == OUTPUT.resolve(), "Open canonical V202 before repairing measurements")
    v202_builder.require(MEASUREMENTS.is_file(), "V202 measurement record is missing")
    v202_builder.require(REJECTED_PRE_REVIEW.is_file(), "Archived pre-review V202 checkpoint is missing")

    current = bpy.data.objects.get("V202_BODY")
    v202_builder.require(current is not None and current.type == "MESH", "Current V202_BODY is missing")

    with bpy.data.libraries.load(str(REJECTED_PRE_REVIEW), link=False) as (source, target):
        v202_builder.require("V202_BODY" in source.objects, "Archived pre-review V202_BODY is missing")
        target.objects = ["V202_BODY"]
    prior = target.objects[0]
    v202_builder.require(prior is not None and prior.type == "MESH", "Could not load archived pre-review body")

    try:
        before_neck = v202_builder.capture_measurements(prior)["neck"]
        after_neck = v202_builder.capture_measurements(current)["neck"]
    finally:
        bpy.data.objects.remove(prior, do_unlink=True)

    record = json.loads(MEASUREMENTS.read_text(encoding="utf-8"))
    record["before"]["neck"] = before_neck
    record["review_before"]["neck"] = before_neck
    record["after"]["neck"] = after_neck
    record["proportion_deltas"]["neck"] = {
        metric: after_neck[metric] - before_neck[metric]
        for metric in ("width_m", "depth_m")
    }
    record["neck_measurement_definition"] = {
        "z_range_m": [1.535, 1.555],
        "x_limit_m": None,
        "baseline_checkpoint": str(REJECTED_PRE_REVIEW.relative_to(ROOT)),
        "reason": "stable upper-neck slice avoids discontinuous trapezius x-cutoff membership",
    }
    write_json(MEASUREMENTS, record)
    ratio = after_neck["width_m"] / before_neck["width_m"]
    print(
        "V202_NECK_MEASUREMENT_REPAIRED "
        f"before={before_neck['width_m']:.9f} after={after_neck['width_m']:.9f} ratio={ratio:.6f}"
    )


if __name__ == "__main__":
    main()
