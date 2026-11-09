"""Report distal high-weight skin vertices for each V250 digit bone."""

from pathlib import Path
import json
import bpy

ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v250_dedicated_hand_rig" / "Character_An_dedicated_hand_rig_v250.blend"
OUT = ROOT / "production_v250_dedicated_hand_rig" / "audit" / "v250_pad_candidates.json"
HAND = "V248_FRETTING_HAND_REALISTIC"


def main():
    if Path(bpy.data.filepath).resolve() != SOURCE.resolve():
        raise RuntimeError(f"Open V250 first: {SOURCE}")
    hand = bpy.data.objects[HAND]
    mesh = hand.data
    group_names = {group.index: group.name for group in hand.vertex_groups}
    record = {"vertex_count": len(mesh.vertices), "digits": {}}
    for digit in ("index", "middle", "ring", "pinky", "thumb"):
        bone_name = f"{digit}_03"
        candidates = []
        for vertex in mesh.vertices:
            weights = {group_names[g.group]: g.weight for g in vertex.groups if g.group in group_names}
            weight = weights.get(bone_name, 0.0)
            if weight < 0.20:
                continue
            world = hand.matrix_world @ vertex.co
            candidates.append({
                "vertex": vertex.index,
                "weight": round(weight, 6),
                "local": [round(float(v), 7) for v in vertex.co],
                "world": [round(float(v), 7) for v in world],
            })
        candidates.sort(key=lambda item: (-item["weight"], item["vertex"]))
        record["digits"][digit] = candidates
    OUT.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("V250_PAD_CANDIDATES=" + json.dumps({k: len(v) for k, v in record["digits"].items()}, sort_keys=True))


if __name__ == "__main__":
    main()
