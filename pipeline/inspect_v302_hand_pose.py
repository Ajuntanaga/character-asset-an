from pathlib import Path
import json

import bpy


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v302_fretting_contact_refinement" / "Character_An_fretting_contact_refinement_v302.blend"

bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
rig = bpy.data.objects["V250_FRETTING_HAND_RIG"]
neck = bpy.data.objects["V206_NECK"]
hand = bpy.data.objects["V248_FRETTING_HAND_REALISTIC"]
to_neck = neck.matrix_world.inverted()

result = {
    "rig_world": [list(row) for row in rig.matrix_world],
    "hand_world": [list(row) for row in hand.matrix_world],
    "bones": {},
}
for digit in ("index", "middle", "ring", "pinky", "thumb"):
    for joint in range(1, 4):
        bone = rig.pose.bones[f"{digit}_{joint:02d}"]
        result["bones"][bone.name] = {
            "head_neck": list(to_neck @ (rig.matrix_world @ bone.head)),
            "tail_neck": list(to_neck @ (rig.matrix_world @ bone.tail)),
        }

print("V302_HAND_POSE=" + json.dumps(result, sort_keys=True))
