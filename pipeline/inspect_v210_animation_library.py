from pathlib import Path

import bpy

source = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An/delivery_v210/Character_An_Performance_v210.blend")
with bpy.data.libraries.load(str(source), link=False) as (data_from, _data_to):
    print({"actions": data_from.actions})
    print({"armatures": data_from.armatures})
    print({"rig_objects": [name for name in data_from.objects if "rig" in name.lower() or "armature" in name.lower()]})
    print({"performance_collections": [name for name in data_from.collections if "208" in name or "209" in name or "performance" in name.lower()]})
