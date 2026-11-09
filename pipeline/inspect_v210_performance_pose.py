from pathlib import Path

import bpy

source = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An/delivery_v210/Character_An_Performance_v210.blend")
with bpy.data.libraries.load(str(source), link=False) as (data_from, data_to):
    data_to.objects = ["V208_PERFORMANCE_RIG"]

rig = data_to.objects[0]
bpy.context.scene.collection.objects.link(rig)
print({"rig": rig.name, "bones": len(rig.pose.bones), "location": list(rig.location)})
for bone in rig.pose.bones:
    name = bone.name.lower()
    if any(key in name for key in ("hand", "forearm", "upper_arm", "thumb", "index", "middle", "ring", "pinky")):
        print({
            "name": bone.name,
            "parent": bone.parent.name if bone.parent else None,
            "head": [round(v, 5) for v in bone.head],
            "tail": [round(v, 5) for v in bone.tail],
            "matrix_translation": [round(v, 5) for v in bone.matrix.translation],
            "matrix_basis": [[round(value, 5) for value in row] for row in bone.matrix_basis],
        })

bpy.data.objects.remove(rig, do_unlink=True)
