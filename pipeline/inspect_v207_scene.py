from __future__ import annotations

import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "production_v206_guitar" / "analysis" / "v207_scene_inventory.json"


def bounds(obj: bpy.types.Object) -> dict[str, list[float]] | None:
    if obj.type not in {"MESH", "CURVE", "SURFACE", "FONT", "META"}:
        return None
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    return {
        "min": [round(min(p[i] for p in points), 6) for i in range(3)],
        "max": [round(max(p[i] for p in points), 6) for i in range(3)],
        "center": [round(sum(p[i] for p in points) / 8.0, 6) for i in range(3)],
    }


def record(obj: bpy.types.Object) -> dict[str, object]:
    return {
        "name": obj.name,
        "type": obj.type,
        "parent": obj.parent.name if obj.parent else None,
        "hidden_render": obj.hide_render,
        "hidden_viewport": obj.hide_viewport,
        "location": [round(v, 6) for v in obj.location],
        "rotation_euler": [round(v, 6) for v in obj.rotation_euler],
        "scale": [round(v, 6) for v in obj.scale],
        "bounds_world": bounds(obj),
        "collections": sorted(c.name for c in obj.users_collection),
    }


tokens = ("HAND", "PALM", "THUMB", "INDEX", "MIDDLE", "RING", "PINKY", "WRIST", "FOREARM", "ARMATURE")
objects = [obj for obj in bpy.data.objects if any(token in obj.name.upper() for token in tokens)]
guitar = [obj for obj in bpy.data.objects if obj.name.startswith("V206_")]
payload = {
    "filepath": bpy.data.filepath,
    "checkpoint": bpy.context.scene.get("checkpoint"),
    "hand_candidates": [record(obj) for obj in sorted(objects, key=lambda item: item.name)],
    "guitar_roots": [record(obj) for obj in sorted(guitar, key=lambda item: item.name) if obj.parent is None],
    "armatures": [record(obj) for obj in sorted(bpy.data.objects, key=lambda item: item.name) if obj.type == "ARMATURE"],
    "collections": sorted(collection.name for collection in bpy.data.collections),
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(f"V207_INVENTORY_OK filepath={bpy.data.filepath} hands={len(objects)} roots={len(payload['guitar_roots'])} armatures={len(payload['armatures'])}")
