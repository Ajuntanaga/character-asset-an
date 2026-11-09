from pathlib import Path

import bpy


library = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An/third_party/blender_human_base_meshes/v1.4.1/human-base-meshes-bundle-v1.4.1/human_base_meshes_bundle.blend")
with bpy.data.libraries.load(str(library), link=False) as (source, target):
    print("COLLECTIONS", sorted(source.collections))
    print("OBJECTS", sorted(source.objects))
    print("ARMATURES", sorted(source.armatures))
    print("ACTIONS", sorted(source.actions))
