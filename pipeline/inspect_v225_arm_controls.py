import bpy

rig = bpy.data.objects["V214_CHARACTER_RIG"]
for bone in rig.pose.bones:
    name = bone.name.lower()
    if any(key in name for key in ("hand_ik", "upper_arm", "forearm", "elbow", "hand_fk", "thumb.01", "f_index.01", "f_middle.01", "f_ring.01", "f_pinky.01")):
        print({
            "name": bone.name,
            "parent": bone.parent.name if bone.parent else None,
            "head": [round(v, 4) for v in bone.head],
            "tail": [round(v, 4) for v in bone.tail],
            "constraints": [constraint.type for constraint in bone.constraints],
            "custom": sorted(bone.keys()),
        })
