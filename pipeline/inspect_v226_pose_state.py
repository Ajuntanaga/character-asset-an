import bpy

rig = bpy.data.objects["V214_CHARACTER_RIG"]
for name in ("hand_ik.R", "hand_ik.L", "upper_arm_ik_target.R", "upper_arm_ik_target.L", "upper_arm_parent.R", "upper_arm_parent.L"):
    bone = rig.pose.bones[name]
    print({
        "name": name,
        "location": [round(v, 4) for v in bone.location],
        "matrix_translation": [round(v, 4) for v in bone.matrix.translation],
        "rotation": [round(v, 4) for v in bone.rotation_euler],
        "ik_fk": bone.get("IK_FK"),
    })
print({"action": rig.animation_data.action.name if rig.animation_data and rig.animation_data.action else None})
for name in ("ORG-hand.R", "ORG-hand.L", "DEF-hand.R", "DEF-hand.L", "ORG-forearm.R", "ORG-forearm.L"):
    bone = rig.pose.bones.get(name)
    if bone:
        print({"name": name, "matrix_translation": [round(v, 4) for v in bone.matrix.translation]})
body = bpy.data.objects.get("V212_IDENTITY_BODY") or bpy.data.objects.get("V214_BODY")
if body:
    print({"body": body.name, "modifiers": [(modifier.type, modifier.object.name if getattr(modifier, "object", None) else None) for modifier in body.modifiers]})
