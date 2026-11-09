from __future__ import annotations

import json

import bpy


payload = {
    "filepath": bpy.data.filepath,
    "scene": bpy.context.scene.name,
    "collections": sorted(collection.name for collection in bpy.data.collections),
    "objects": [
        {
            "name": obj.name,
            "type": obj.type,
            "parent": obj.parent.name if obj.parent else None,
            "hide_render": obj.hide_render,
        }
        for obj in bpy.data.objects
        if obj.name.startswith(("V196_", "V206_", "V207_"))
    ],
}
print("V236_LIVE_INSPECT=" + json.dumps(payload, sort_keys=True))
