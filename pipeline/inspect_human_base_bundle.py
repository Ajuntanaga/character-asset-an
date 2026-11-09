"""Read-only inventory of bundled Human Base Meshes datablocks."""

from pathlib import Path
import json
import bpy

ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
BUNDLE = ROOT / "third_party/blender_human_base_meshes/v1.4.1/human-base-meshes-bundle-v1.4.1/human_base_meshes_bundle.blend"
OUT = ROOT / "third_party/blender_human_base_meshes/v1.4.1/bundle_inventory.json"

with bpy.data.libraries.load(str(BUNDLE), link=False) as (source, target):
    record = {
        "objects": sorted(source.objects),
        "collections": sorted(source.collections),
        "armatures": sorted(source.armatures),
        "meshes": sorted(source.meshes),
        "actions": sorted(source.actions),
    }
OUT.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print("HUMAN_BASE_BUNDLE_INVENTORY=" + json.dumps({k: len(v) for k, v in record.items()}, sort_keys=True))
