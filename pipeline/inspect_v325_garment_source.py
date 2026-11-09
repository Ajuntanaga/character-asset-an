"""Measure garment extraction regions on the corrected male body."""

from collections import Counter
from pathlib import Path
import json

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v324_identity_cleanup" / "Character_An_identity_cleanup_v324.blend"
OUTPUT = ROOT / "production_v324_identity_cleanup" / "audit" / "v325_garment_source_probe.json"


def center_world(obj, polygon):
    return obj.matrix_world @ polygon.center


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    body = bpy.data.objects["V322_MB_MALE_BODY"]
    material_counts = Counter(poly.material_index for poly in body.data.polygons)
    material_names = {
        index: slot.material.name if slot.material else None
        for index, slot in enumerate(body.material_slots)
    }
    candidates = Counter()
    ranges = {}
    for poly in body.data.polygons:
        if poly.material_index != 0:
            continue
        center = center_world(body, poly)
        x, y, z = center
        if 0.80 <= z <= 1.55 and abs(x) < 0.73:
            candidates["jacket_all"] += 1
            if not (y < -0.07 and abs(x) < 0.105 and z > 0.88):
                candidates["jacket_open_front"] += 1
        if 0.82 <= z <= 1.55 and abs(x) < 0.29:
            candidates["shirt_torso"] += 1
        if 0.15 <= z <= 1.00:
            candidates["pants"] += 1
        for label in ("jacket_all", "shirt_torso", "pants"):
            if label not in ranges:
                ranges[label] = {"min": [1e9] * 3, "max": [-1e9] * 3}
    vertices = [body.matrix_world @ vertex.co for vertex in body.data.vertices]
    report = {
        "source": str(SOURCE),
        "body": body.name,
        "vertex_count": len(body.data.vertices),
        "polygon_count": len(body.data.polygons),
        "material_names": material_names,
        "material_polygon_counts": dict(material_counts),
        "source_bounds_m": {
            "min": [min(point[axis] for point in vertices) for axis in range(3)],
            "max": [max(point[axis] for point in vertices) for axis in range(3)],
        },
        "candidate_polygon_counts": dict(candidates),
        "vertex_group_count": len(body.vertex_groups),
        "armature_modifiers": [
            {"name": mod.name, "object": mod.object.name if mod.object else None}
            for mod in body.modifiers if mod.type == "ARMATURE"
        ],
    }
    OUTPUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print("V325_GARMENT_SOURCE_PROBE_OK=" + json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
