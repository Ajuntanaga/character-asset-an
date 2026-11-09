"""Read-only inventory of the installed Human Base Meshes bundle."""

from pathlib import Path
import json

import bpy


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
LIBRARY = ROOT / "third_party/blender_human_base_meshes/v1.4.1/human-base-meshes-bundle-v1.4.1/human_base_meshes_bundle.blend"
OUT = ROOT / "production_v300_guitar_visual_acceptance" / "audit" / "human_base_mesh_library_inventory.json"


def main():
    with bpy.data.libraries.load(str(LIBRARY), link=False) as (source, _target):
        names = list(source.objects)
    selected = [name for name in names if any(token in name.lower() for token in ("hand", "male", "body", "human", "armature", "animation"))]
    record = {
        "schema": "human-base-mesh-library-inventory-v1",
        "library": str(LIBRARY.relative_to(ROOT)),
        "object_count": len(names),
        "selected_object_names": selected,
        "all_object_names": names,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("HUMAN_BASE_MESH_LIBRARY_INVENTORY=" + json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
