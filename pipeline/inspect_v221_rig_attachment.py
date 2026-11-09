from pathlib import Path

import bpy

source = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An/production_v221_identity_cleanup/Character_An_identity_cleanup_v221.blend")
bpy.ops.wm.open_mainfile(filepath=str(source))

rig = bpy.data.objects.get("V214_CHARACTER_RIG")
if rig is None:
    raise RuntimeError("V214 rig missing")

print({"rig": rig.name, "bones": len(rig.pose.bones)})
for bone in rig.pose.bones:
    lower = bone.name.lower()
    if "head" in lower or lower in {"neck", "neck.001", "spine.006"}:
        print({
            "bone": bone.name,
            "parent": bone.parent.name if bone.parent else None,
            "head": [round(value, 4) for value in bone.head],
            "tail": [round(value, 4) for value in bone.tail],
            "deform": bone.bone.use_deform,
        })
