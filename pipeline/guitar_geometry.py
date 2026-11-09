from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MAPPING_PATH = ROOT / "references" / "m3" / "m3_chord_mapping_v2.json"


def fret_distance(scale_m: float, fret: int) -> float:
    if scale_m <= 0.0:
        raise ValueError("scale length must be positive")
    if not 0 <= fret <= 24:
        raise ValueError(f"fret must be in 0..24: {fret}")
    return scale_m * (1.0 - 2.0 ** (-fret / 12.0))


def load_authoritative_mapping(path: Path = MAPPING_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


@dataclass(frozen=True)
class StringSpec:
    id: str
    tuning: str
    scale_m: float
    nut_y_m: float
    bridge_y_m: float


@dataclass(frozen=True)
class GuitarGeometry:
    strings: dict[str, StringSpec]
    fret_count: int
    neutral_fret: int

    @property
    def string_ids_low_to_high(self) -> tuple[str, ...]:
        return tuple(f"S{index}" for index in range(1, 9))

    @classmethod
    def from_mapping(cls, mapping: dict[str, Any]) -> "GuitarGeometry":
        try:
            convention = mapping["coordinate_convention"]
            instrument = mapping["instrument_geometry"]
            tuning = tuple(convention["tuning_low_to_high"])
            scales = instrument["scale_lengths_by_m3_string_in"]
            fret_count = int(instrument["frets"])
            neutral_fret = int(instrument["neutral_fret"])
            nut_spread_m = float(instrument["nut_string_spread_mm"]) / 1000.0
            bridge_spread_m = float(instrument["bridge_string_spacing_mm"]) * 7.0 / 1000.0
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(f"malformed M3 mapping: {error}") from error

        if len(tuning) != 8 or fret_count != 24 or neutral_fret != 7:
            raise ValueError("M3 mapping must define eight tunings, 24 frets, and neutral F7")
        expected_ids = tuple(f"S{index}" for index in range(1, 9))
        if set(scales) != set(expected_ids):
            raise ValueError("M3 mapping must define scale lengths for S1..S8")
        if abs(nut_spread_m - 0.049) > 1e-12 or abs(bridge_spread_m - 0.0735) > 1e-12:
            raise ValueError("M3 mapping string spreads disagree with the approved contract")

        specs: dict[str, StringSpec] = {}
        for index, string_id in enumerate(expected_ids):
            fraction = index / 7.0
            specs[string_id] = StringSpec(
                id=string_id,
                tuning=str(tuning[index]),
                scale_m=float(scales[string_id]) * 0.0254,
                nut_y_m=-nut_spread_m / 2.0 + nut_spread_m * fraction,
                bridge_y_m=-bridge_spread_m / 2.0 + bridge_spread_m * fraction,
            )
        return cls(strings=specs, fret_count=fret_count, neutral_fret=neutral_fret)

    def _spec(self, string_id: str) -> StringSpec:
        try:
            return self.strings[string_id]
        except KeyError as error:
            raise ValueError(f"unknown string id: {string_id}") from error

    def _point_at_distance(self, spec: StringSpec, x_m: float) -> tuple[float, float, float]:
        progress = max(0.0, min(1.0, x_m / spec.scale_m))
        y_m = spec.nut_y_m + (spec.bridge_y_m - spec.nut_y_m) * progress
        return (x_m, y_m, 0.0)

    def string_fret_wire_point(self, string_id: str, fret: int) -> tuple[float, float, float]:
        spec = self._spec(string_id)
        return self._point_at_distance(spec, fret_distance(spec.scale_m, fret))

    def string_pad_point(
        self,
        string_id: str,
        fret: int,
        behind_fraction: float = 0.18,
    ) -> tuple[float, float, float]:
        spec = self._spec(string_id)
        if not 1 <= fret <= self.fret_count:
            raise ValueError(f"a behind-fret pad point requires fret 1..{self.fret_count}: {fret}")
        if not 0.0 < behind_fraction < 1.0:
            raise ValueError("behind_fraction must be between 0 and 1")
        wire_x = fret_distance(spec.scale_m, fret)
        prior_x = fret_distance(spec.scale_m, fret - 1)
        pad_x = wire_x - behind_fraction * (wire_x - prior_x)
        return self._point_at_distance(spec, pad_x)

    def local_wire_from_neutral(self, string_id: str, fret: int) -> tuple[float, float, float]:
        spec = self._spec(string_id)
        point = self.string_fret_wire_point(string_id, fret)
        neutral_x = fret_distance(spec.scale_m, self.neutral_fret)
        return (point[0] - neutral_x, point[1], point[2])

    def local_pad_from_neutral(
        self,
        string_id: str,
        fret: int,
        behind_fraction: float = 0.18,
    ) -> tuple[float, float, float]:
        spec = self._spec(string_id)
        point = self.string_pad_point(string_id, fret, behind_fraction)
        neutral_x = fret_distance(spec.scale_m, self.neutral_fret)
        return (point[0] - neutral_x, point[1], point[2])

    def local_from_neutral(
        self,
        string_id: str,
        fret: int,
        behind_fraction: float = 0.18,
    ) -> tuple[float, float, float]:
        """Return the pad center, never the fret-wire intersection."""
        return self.local_pad_from_neutral(string_id, fret, behind_fraction)

    def fret_wire_segment(
        self,
        fret: int,
    ) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
        return (
            self.string_fret_wire_point("S1", fret),
            self.string_fret_wire_point("S8", fret),
        )


def string_fret_point(
    string_id: str,
    fret: int,
    behind_fraction: float = 0.18,
) -> tuple[float, float, float]:
    """Compatibility entry point returning the canonical pad center from nut."""
    return GuitarGeometry.from_mapping(load_authoritative_mapping()).string_pad_point(
        string_id, fret, behind_fraction
    )
