import json
import bpy

rig = bpy.data.objects["V239_CLEAN_CHARACTER_RIG"]
names = [
    name for name in rig.pose.bones.keys()
    if any(token in name for token in ("upper_arm_parent", "thigh_parent", "foot_parent", "hand_fk", "foot_fk"))
]
record = {}
for name in sorted(names):
    bone = rig.pose.bones[name]
    record[name] = {key: bone[key] for key in bone.keys() if key != "_RNA_UI"}
print("V277_RIG_PROPS=" + json.dumps(record, sort_keys=True, default=str))
samples = {}
for frame in (1, 10, 20, 40, 50, 60, 80, 90):
    bpy.context.scene.frame_set(frame)
    bpy.context.view_layer.update()
    samples[frame] = {
        "arm_parent_ik_fk": rig.pose.bones["upper_arm_parent.L"].get("IK_FK"),
        "leg_parent_ik_fk": rig.pose.bones["thigh_parent.L"].get("IK_FK"),
        "upper_arm_fk_matrix": [round(v, 5) for row in rig.pose.bones["upper_arm_fk.L"].matrix for v in row],
        "def_upper_arm_matrix": [round(v, 5) for row in rig.pose.bones["DEF-upper_arm.L"].matrix for v in row],
        "thigh_fk_matrix": [round(v, 5) for row in rig.pose.bones["thigh_fk.L"].matrix for v in row],
        "def_thigh_matrix": [round(v, 5) for row in rig.pose.bones["DEF-thigh.L"].matrix for v in row],
    }
print("V277_RIG_SAMPLES=" + json.dumps(samples, sort_keys=True))
chain = {}
for name in sorted(
    n for n in rig.pose.bones.keys()
    if any(token in n for token in ("upper_arm", "forearm", "thigh", "shin")) and n.endswith(".L")
):
    bone = rig.pose.bones[name]
    if bone.constraints:
        chain[name] = [
            {
                "name": constraint.name,
                "type": constraint.type,
                "influence": constraint.influence,
                "mute": constraint.mute,
                "subtarget": getattr(constraint, "subtarget", ""),
            }
            for constraint in bone.constraints
        ]
print("V277_CONSTRAINT_CHAIN=" + json.dumps(chain, sort_keys=True))
