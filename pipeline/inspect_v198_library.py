from pathlib import Path

import bpy

source = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An/production_v198_deformation/ant_deformation_ready_v198.blend")
with bpy.data.libraries.load(str(source), link=False) as (data_from, _data_to):
    print({"collections": data_from.collections})
    print({"armatures": data_from.armatures})
    print({"actions": data_from.actions})
    print({"rig_objects": [name for name in data_from.objects if "rig" in name.lower() or "armature" in name.lower()]})
    print({"body_head_objects": [name for name in data_from.objects if any(key in name.lower() for key in ("body", "head", "face", "skin", "guitar", "hand"))][:300]})
