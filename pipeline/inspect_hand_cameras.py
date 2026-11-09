import bpy

for obj in sorted(bpy.data.objects, key=lambda item: item.name):
    if obj.type == "CAMERA":
        print("CAMERA", obj.name)
