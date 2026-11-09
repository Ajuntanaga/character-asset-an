from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pipeline.common import project_root, sha256

SCHEMA = "photoreal-stage-record-v1"


def _stored_path(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path.resolve())


def make_stage_record(stage: str, source: Path, output: Path, artifacts: list[Path], validation: dict[str, object]) -> dict[str, object]:
    source, output = source.resolve(), output.resolve()
    artifact_root = project_root().resolve()
    if not all(path.resolve().is_relative_to(artifact_root) for path in artifacts):
        raise ValueError("artifacts must be inside the project root")
    return {
        "schema": SCHEMA,
        "stage": stage,
        "timestamp_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source": {"path": _stored_path(source, project_root()), "bytes": source.stat().st_size, "sha256": sha256(source)},
        "output": {"path": _stored_path(output, project_root()), "bytes": output.stat().st_size, "sha256": sha256(output)},
        "artifacts": [{"path": _stored_path(path, artifact_root), "bytes": path.stat().st_size, "sha256": sha256(path)} for path in artifacts],
        "validation": validation,
    }


def validate_stage_record(record: dict[str, object], expected_stage: str) -> list[str]:
    errors: list[str] = []
    if record.get("schema") != SCHEMA:
        errors.append("schema:invalid")
    if record.get("stage") != expected_stage:
        errors.append(f"stage:expected {expected_stage} got {record.get('stage')}")
    root = project_root().resolve()
    for label in ("source", "output"):
        item = record.get(label)
        if not isinstance(item, dict) or not item.get("sha256"):
            errors.append(f"{label}:missing_sha256")
            continue
        path = Path(item.get("path", ""))
        if not path.is_absolute():
            path = root / path
        if not path.is_file():
            errors.append(f"{label}:missing")
        elif sha256(path) != item["sha256"]:
            errors.append(f"{label}:sha256_mismatch")
    artifact_root = root
    for item in record.get("artifacts", []):
        if not isinstance(item, dict) or not item.get("path"):
            errors.append("artifact:missing_path")
            continue
        path_text = str(item["path"])
        path = Path(path_text)
        if path.is_absolute():
            errors.append("artifact:absolute_path")
            continue
        resolved = (artifact_root / path).resolve()
        if not resolved.is_relative_to(artifact_root) or not resolved.is_file():
            errors.append("artifact:missing_or_outside")
        elif not item.get("sha256"):
            errors.append("artifact:missing_sha256")
        elif sha256(resolved) != item["sha256"]:
            errors.append("artifact:sha256_mismatch")
    validation = record.get("validation")
    if not isinstance(validation, dict) or validation.get("status") != "PASS":
        errors.append("validation:status_not_PASS")
    return sorted(set(errors))
