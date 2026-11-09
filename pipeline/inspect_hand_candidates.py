"""Append candidate hand/body objects temporarily and record their topology."""

from pathlib import Path
import json

import bpy


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
LIBRARY = ROOT / "third_party/blender_human_base_meshes/v1.4.1/human-base-meshes-bundle-v1.4.1/human_base_meshes_bundle.blend"
OUT = ROOT / "production_v300_guitar_visual_acceptance" / "audit" / "hand_candidate_topology.json"
CANDIDATES = (
    "realistic_hand",
    "Hand  - Realistic",
    "realistic_body_male",
    "GEO-body_male_realistic",
    "GEO-hand_male_primitive_realistic.L",
    "GEO-finger_index_male_primitive_realistic.L",
)


def main():
    with bpy.data.libraries.load(str(LIBRARY), link=False) as (_source, target):
        target.objects = list(CANDIDATES)
    rows = []
    for obj in target.objects:
        if obj is None:
            continue
        data = obj.data
        rows.append({
            "name": obj.name,
            "type": obj.type,
            "vertices": len(data.vertices) if obj.type == "MESH" else None,
            "edges": len(data.edges) if obj.type == "MESH" else None,
            "polygons": len(data.polygons) if obj.type == "MESH" else None,
            "dimensions": [float(value) for value in obj.dimensions],
            "vertex_groups": [group.name for group in obj.vertex_groups],
            "modifiers": [modifier.type for modifier in obj.modifiers],
            "materials": [material.name for material in data.materials if material] if hasattr(data, "materials") else [],
            "parent": obj.parent.name if obj.parent else None,
            "shape_keys": list(data.shape_keys.key_blocks.keys()) if obj.type == "MESH" and data.shape_keys else [],
        })
    record = {"schema": "hand-candidate-topology-v1", "library": str(LIBRARY.relative_to(ROOT)), "candidates": rows}
    OUT.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("HAND_CANDIDATE_TOPOLOGY=" + json.dumps(record, sort_keys=True))
    for obj in target.objects:
        if obj is not None:
            bpy.data.objects.remove(obj, do_unlink=True)


if __name__ == "__main__":
    main()
