from pathlib import Path
import json

import bpy

ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v307_charmorph_reom_rig" / "Character_An_reom_rig_v307.blend"
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
rig = bpy.data.objects["V307_REOM_RIG"]
names = [
    name for name in rig.pose.bones.keys()
    if name.endswith(".L") and any(token in name for token in ("f_index", "f_middle", "f_ring", "f_pinky", "thumb", "palm"))
]
record = {}
for name in sorted(names):
    bone = rig.pose.bones[name]
    record[name] = {
        "rotation_mode": bone.rotation_mode,
        "custom": {key: bone[key] for key in bone.keys() if key != "_RNA_UI" and isinstance(bone[key], (int, float, str, bool))},
        "constraints": [{"name": constraint.name, "type": constraint.type, "influence": constraint.influence} for constraint in bone.constraints],
        "head": list(bone.head),
        "tail": list(bone.tail),
    }
print("V307_FINGER_CONTROLS=" + json.dumps(record, sort_keys=True))
