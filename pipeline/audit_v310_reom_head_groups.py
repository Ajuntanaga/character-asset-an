"""Report Reom vertex groups suitable for a non-destructive head mask."""

from pathlib import Path
import json

import bpy


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v310_reom_scene_alignment" / "Character_An_reom_scene_alignment_v310.blend"


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    body = bpy.data.objects["V310_REOM_BODY"]
    names = {group.index: group.name for group in body.vertex_groups}
    relevant = [name for name in names.values() if any(token in name.lower() for token in ("head", "neck", "face", "jaw", "spine.006", "spine.005"))]
    counts = {}
    for name in relevant:
        index = body.vertex_groups[name].index
        weighted = [(vertex.index, item.weight) for vertex in body.data.vertices for item in vertex.groups if item.group == index and item.weight > 0.01]
        counts[name] = {"vertices": len(weighted), "max_weight": max((weight for _vertex, weight in weighted), default=0.0)}
    print("V310_REOM_HEAD_GROUPS=" + json.dumps({"groups": relevant, "counts": counts}, sort_keys=True))


if __name__ == "__main__":
    main()
