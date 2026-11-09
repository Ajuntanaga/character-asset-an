"""Inventory guitar neck/fret/string geometry and world-space bounds in V250."""

from pathlib import Path
import json
import bpy

ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v250_dedicated_hand_rig" / "Character_An_dedicated_hand_rig_v250.blend"
OUT = ROOT / "production_v250_dedicated_hand_rig" / "audit" / "v250_guitar_geometry.json"
TOKENS = ("guitar", "neck", "fret", "string", "fingerboard", "bridge", "nut")


def main():
    if Path(bpy.data.filepath).resolve() != SOURCE.resolve():
        raise RuntimeError(f"Open V250 first: {SOURCE}")
    rows = []
    for obj in bpy.context.scene.objects:
        if obj.type not in {"MESH", "CURVE"} or not any(token in obj.name.lower() for token in TOKENS):
            continue
        corners = [obj.matrix_world @ __import__("mathutils").Vector(corner) for corner in obj.bound_box]
        rows.append({
            "name": obj.name,
            "type": obj.type,
            "vertices": len(obj.data.vertices) if obj.type == "MESH" else None,
            "dimensions_m": [round(float(v), 6) for v in obj.dimensions],
            "bbox_min_world_m": [round(min(float(c[i]) for c in corners), 7) for i in range(3)],
            "bbox_max_world_m": [round(max(float(c[i]) for c in corners), 7) for i in range(3)],
            "location_world_m": [round(float(v), 7) for v in obj.matrix_world.translation],
            "matrix_world": [[round(float(obj.matrix_world[r][c]), 8) for c in range(4)] for r in range(4)],
            "vertices_local_m": [[round(float(v), 7) for v in vertex.co] for vertex in obj.data.vertices] if obj.type == "MESH" and obj.name in {"V206_NECK", "V206_FRETBOARD"} else None,
            "spline_points_local_m": [
                [round(float(point.co[i]), 7) for i in range(3)]
                for spline in obj.data.splines
                for point in spline.points
            ] if obj.type == "CURVE" and obj.name.startswith("V206_STRING_S") else None,
            "visible_render": not obj.hide_render,
        })
    rows.sort(key=lambda row: row["name"])
    OUT.write_text(json.dumps({"schema": "v250-guitar-geometry-v1", "objects": rows}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("V250_GUITAR_GEOMETRY=" + json.dumps({"count": len(rows), "names": [r["name"] for r in rows]}, sort_keys=True))


if __name__ == "__main__":
    main()
