from pathlib import Path

import bpy

source = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An/production_v206_guitar/ant_headless_guitar_v206.blend")
with bpy.data.libraries.load(str(source), link=False) as (data_from, _data_to):
    print({"collections": data_from.collections})
    print({"v206_objects": [name for name in data_from.objects if name.startswith("V206") or name.startswith("M3_")]})
    print({"guitar_objects": [name for name in data_from.objects if any(key in name.lower() for key in ("guitar", "fret", "string", "pickup", "bridge", "neck"))][:300]})
