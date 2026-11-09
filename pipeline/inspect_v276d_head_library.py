import json
from pathlib import Path

import bpy

ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
LIBRARY = ROOT / "third_party/blender_human_base_meshes/v1.4.1/human-base-meshes-bundle-v1.4.1/human_base_meshes_bundle.blend"

with bpy.data.libraries.load(str(LIBRARY), link=False) as (data_from, _data_to):
    library_names = {
        "collections": [name for name in data_from.collections if "jaw" in name.lower() or "head" in name.lower()],
        "objects": [name for name in data_from.objects if "jaw" in name.lower() or "head_animation" in name.lower()],
        "meshes": [name for name in data_from.meshes if "jaw" in name.lower() or "head_animation" in name.lower()],
    }

scene_records = {}
for obj in bpy.data.objects:
    if obj.name.startswith("V276D_GEO-head_animation"):
        scene_records[obj.name] = {
            "parent": obj.parent.name if obj.parent else None,
            "parent_type": obj.parent_type,
            "location": list(obj.location),
            "world_translation": list(obj.matrix_world.translation),
            "dimensions": list(obj.dimensions),
            "bound_box_center_world": list(sum((obj.matrix_world @ __import__('mathutils').Vector(corner) for corner in obj.bound_box), __import__('mathutils').Vector()) / 8.0),
        }

print("V276D_LIBRARY=" + json.dumps(library_names, sort_keys=True))
print("V276D_SCENE_HIERARCHY=" + json.dumps(scene_records, sort_keys=True))
