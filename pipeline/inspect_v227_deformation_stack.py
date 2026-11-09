import bpy

for obj in bpy.data.objects:
    if obj.type == "MESH" and (obj.name.startswith("V219_") or "BODY" in obj.name):
        print({
            "name": obj.name,
            "vertices": len(obj.data.vertices),
            "groups": len(obj.vertex_groups),
            "group_sample": [group.name for group in list(obj.vertex_groups)[:12]],
            "modifiers": [(modifier.name, modifier.type, modifier.object.name if getattr(modifier, "object", None) else None) for modifier in obj.modifiers],
        })
