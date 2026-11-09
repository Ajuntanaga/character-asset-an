from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def project_root() -> Path:
    return PROJECT_ROOT


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def blender_args() -> list[str]:
    return sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []


def rounded(values: Iterable[float], digits: int = 7) -> list[float]:
    return [round(float(value), digits) for value in values]


def _fingerprint_object(obj: Any) -> dict[str, Any]:
    record: dict[str, Any] = {
        "name": obj.name,
        "type": obj.type,
        "hide_render": bool(obj.hide_render),
        "hide_viewport": bool(obj.hide_viewport),
        "matrix_world": [round(float(value), 7) for row in obj.matrix_world for value in row],
        "materials": [slot.material.name if slot.material else None for slot in obj.material_slots],
    }
    if obj.type == "MESH":
        record["vertices"] = [rounded(vertex.co) for vertex in obj.data.vertices]
        record["polygons"] = [list(polygon.vertices) for polygon in obj.data.polygons]
    elif obj.type == "CURVE":
        splines = []
        for spline in obj.data.splines:
            entry: dict[str, Any] = {"type": spline.type, "cyclic": spline.use_cyclic_u}
            if spline.type == "BEZIER":
                entry["points"] = [
                    {
                        "co": rounded(point.co),
                        "left": rounded(point.handle_left),
                        "right": rounded(point.handle_right),
                        "radius": round(float(point.radius), 7),
                    }
                    for point in spline.bezier_points
                ]
            else:
                entry["points"] = [
                    {"co": rounded(point.co), "radius": round(float(point.radius), 7)}
                    for point in spline.points
                ]
            splines.append(entry)
        record["splines"] = splines
    return record


def snapshot_objects(excluded: set[str] | None = None, excluded_prefixes: tuple[str, ...] = ()) -> dict[str, Any]:
    import bpy

    excluded = excluded or set()
    records = [
        _fingerprint_object(obj)
        for obj in sorted(bpy.data.objects, key=lambda item: item.name)
        if obj.name not in excluded and not obj.name.startswith(excluded_prefixes)
    ]
    payload = json.dumps(records, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {"count": len(records), "sha256": hashlib.sha256(payload).hexdigest()}


def ensure_material(name: str, base_color: tuple[float, float, float, float], roughness: float = 0.5):
    import bpy

    material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.diffuse_color = base_color
    material.use_nodes = True
    principled = material.node_tree.nodes.get("Principled BSDF")
    if principled:
        principled.inputs["Base Color"].default_value = base_color
        principled.inputs["Roughness"].default_value = roughness
    return material


def link_object_like(source: Any, duplicate: Any) -> None:
    collections = list(source.users_collection)
    if not collections:
        raise RuntimeError(f"Object has no collection: {source.name}")
    for collection in collections:
        collection.objects.link(duplicate)
