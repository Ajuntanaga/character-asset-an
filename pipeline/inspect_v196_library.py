from pathlib import Path
import json
import bpy

root = Path(__file__).resolve().parents[1]
source = root / "production_v196_hands" / "ant_anatomical_hands_v196.blend"
with bpy.data.libraries.load(str(source), link=False) as (data_from, data_to):
    payload = {
        "objects": sorted(name for name in data_from.objects if any(token in name for token in ("FRETTING", "V196", "V190"))),
        "materials": sorted(name for name in data_from.materials if any(token in name for token in ("HAND", "SKIN", "NAIL", "V196"))),
        "collections": sorted(data_from.collections),
    }
out = root / "production_v206_guitar" / "analysis" / "v196_library_inventory.json"
out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(f"V196_LIBRARY_OK objects={len(payload['objects'])} materials={len(payload['materials'])}")
