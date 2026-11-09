import json
import bpy

records = []
for obj in bpy.context.scene.objects:
    name = obj.name.lower()
    if any(token in name for token in ("head", "face", "eye", "jaw", "teeth", "tongue", "brow", "lash")):
        shape_keys = []
        if getattr(obj.data, "shape_keys", None):
            shape_keys = [key.name for key in obj.data.shape_keys.key_blocks]
        records.append({
            "name": obj.name,
            "type": obj.type,
            "hidden": bool(obj.hide_render),
            "parent": obj.parent.name if obj.parent else None,
            "parent_bone": obj.parent_bone,
            "shape_keys": shape_keys,
        })
print("V271_FACE_ANIMATION=" + json.dumps(records, sort_keys=True))
