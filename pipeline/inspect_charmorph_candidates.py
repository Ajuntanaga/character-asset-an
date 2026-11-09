from pathlib import Path
import json

import bpy


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
DATA = ROOT / "third_party" / "charmorph" / "v0.4.0-3" / "CharMorph-data" / "characters"
OUTPUT = ROOT / "third_party" / "charmorph" / "v0.4.0-3" / "candidate_inventory.json"
bpy.ops.wm.read_homefile(use_empty=True, use_factory_startup=True)
records = {}
for candidate in ("mb_male", "reom", "antonia"):
    blend = DATA / candidate / "char.blend"
    with bpy.data.libraries.load(str(blend), link=False) as (source, target):
        target.objects = list(source.objects)
    objects = [obj for obj in target.objects if obj]
    records[candidate] = {
        "path": str(blend.relative_to(ROOT)),
        "objects": [
            {
                "name": obj.name,
                "type": obj.type,
                "vertices": len(obj.data.vertices) if obj.type == "MESH" else None,
                "polygons": len(obj.data.polygons) if obj.type == "MESH" else None,
                "dimensions": list(obj.dimensions),
                "vertex_groups": len(obj.vertex_groups) if obj.type == "MESH" else None,
                "shape_keys": len(obj.data.shape_keys.key_blocks) if obj.type == "MESH" and obj.data.shape_keys else 0,
                "materials": [material.name if material else None for material in obj.data.materials] if obj.type == "MESH" else [],
            }
            for obj in objects
        ],
    }
    for obj in objects:
        bpy.data.objects.remove(obj, do_unlink=True)
OUTPUT.write_text(json.dumps(records, indent=2, sort_keys=True) + "\n")
print("CHARMORPH_CANDIDATES=" + json.dumps(records, sort_keys=True))
