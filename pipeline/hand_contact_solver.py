from __future__ import annotations

from dataclasses import dataclass

from pipeline.guitar_geometry import GuitarGeometry, load_authoritative_mapping


APPROVED_TARGETS = (
    ("index", "S5", 9),
    ("middle", "S4", 10),
    ("ring", "S7", 9),
    ("pinky", "S8", 11),
)


@dataclass(frozen=True)
class FingerTarget:
    finger: str
    string_id: str
    fret: int
    pad_point: tuple[float, float, float]


@dataclass(frozen=True)
class HandSolveReport:
    status: str
    targets: tuple[FingerTarget, ...]
    joint_angles_deg: dict[str, tuple[float, float, float]]
    minimum_clearance_m: float
    collisions: tuple[str, ...]
    thumb_behind_neck: bool = True
    thumb_crosses_top_edge: bool = False
    wrist_flexion_deg: float = 0.0
    wrist_deviation_deg: float = 0.0
    fretboard_penetration_m: float = 0.0
    minimum_string_depression_m: float = 0.0003


def build_candidate_targets(geometry: GuitarGeometry) -> tuple[FingerTarget, ...]:
    return tuple(
        FingerTarget(
            finger=finger,
            string_id=string_id,
            fret=fret,
            pad_point=geometry.local_pad_from_neutral(string_id, fret, behind_fraction=0.18),
        )
        for finger, string_id, fret in APPROVED_TARGETS
    )


def _distance(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return sum((left - right) ** 2 for left, right in zip(a, b)) ** 0.5


def validate_hand_solve(
    report: HandSolveReport,
    geometry: GuitarGeometry | None = None,
) -> list[str]:
    geometry = geometry or GuitarGeometry.from_mapping(load_authoritative_mapping())
    errors: list[str] = []

    actual_map = {(target.finger, target.string_id, target.fret) for target in report.targets}
    expected_map = set(APPROVED_TARGETS)
    if actual_map != expected_map or len(report.targets) != 4:
        errors.append(f"target map mismatch: expected {sorted(expected_map)}, got {sorted(actual_map)}")
    if len({target.finger for target in report.targets}) != len(report.targets):
        errors.append("each target must use a distinct finger")

    for target in report.targets:
        try:
            canonical_pad = geometry.local_pad_from_neutral(target.string_id, target.fret, behind_fraction=0.18)
            wire = geometry.local_wire_from_neutral(target.string_id, target.fret)
        except ValueError as error:
            errors.append(str(error))
            continue
        if _distance(target.pad_point, wire) < 1e-6:
            errors.append(f"{target.finger} contact is on the fret wire, not behind it")
        if _distance(target.pad_point, canonical_pad) > 0.00025:
            errors.append(f"{target.finger} pad center misses canonical {target.string_id}/F{target.fret}")

    for joint_name, angles in report.joint_angles_deg.items():
        if len(angles) != 3:
            errors.append(f"{joint_name} must report MCP/PIP/DIP angles")
            continue
        if any(angle < 0.0 for angle in angles):
            errors.append(f"{joint_name} hyperextension is not allowed: {angles}")
        if any(angle > limit for angle, limit in zip(angles, (95.0, 115.0, 90.0))):
            errors.append(f"{joint_name} exceeds flexion bounds: {angles}")

    if report.collisions:
        errors.append(f"collision list is not empty: {report.collisions}")
    if report.minimum_clearance_m <= 0.0:
        errors.append(f"adjacent-string clearance must be positive: {report.minimum_clearance_m}")
    if not report.thumb_behind_neck or report.thumb_crosses_top_edge:
        errors.append("thumb must remain behind the neck and below the fretboard top edge")
    if abs(report.wrist_flexion_deg) > 30.0 or abs(report.wrist_deviation_deg) > 20.0:
        errors.append(
            f"wrist bounds exceeded: flexion={report.wrist_flexion_deg}, deviation={report.wrist_deviation_deg}"
        )
    if report.fretboard_penetration_m > 0.0:
        errors.append(f"fretboard penetration is {report.fretboard_penetration_m} m")
    if report.minimum_string_depression_m < 0.0002:
        errors.append(
            f"string depression is not visibly established: {report.minimum_string_depression_m} m"
        )
    if report.status != "PASS":
        errors.append(f"solver status is {report.status}, not PASS")
    return errors
