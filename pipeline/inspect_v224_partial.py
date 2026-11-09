import bpy

print({"filepath": bpy.data.filepath})
print({"cameras": [obj.name for obj in bpy.data.objects if obj.type == "CAMERA"]})
print({"collections": [collection.name for collection in bpy.context.scene.collection.children]})
print({"guitar_objects": len([obj for obj in bpy.data.objects if obj.name.startswith("V206_")])})
