import json

import bpy


print(
    "LIVE_CHECKPOINT="
    + json.dumps(
        {
            "filepath": bpy.data.filepath,
            "scene": bpy.context.scene.name,
            "v240_status": bpy.context.scene.get("V240_STATUS"),
        },
        sort_keys=True,
    )
)
