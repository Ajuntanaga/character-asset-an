import bpy

root = bpy.data.objects.get("V206_GUITAR_ROOT")
print({
    "root": root.name if root else None,
    "type": root.type if root else None,
    "location": list(root.location) if root else None,
    "rotation": list(root.rotation_euler) if root else None,
    "scale": list(root.scale) if root else None,
    "children": len(root.children_recursive) if root else None,
})
for name in ("V206_BODY_CORE", "V206_NECK", "V206_FRETBOARD"):
    obj = bpy.data.objects.get(name)
    print({"name": name, "parent": obj.parent.name if obj and obj.parent else None, "dimensions": list(obj.dimensions) if obj else None})
