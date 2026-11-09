import bpy

print("CHECKPOINT", bpy.context.scene.get("checkpoint"))
print("FILE", bpy.data.filepath)
for obj in sorted(bpy.data.objects, key=lambda item: item.name):
    if obj.name.startswith("V194") or obj.name in {"V163_BODY_FAILED_PICKING_HAND_MASKED", "V131_CLEAN_CONNECTED_SHORT_CURL_HAIR"}:
        print("OBJECT", obj.name, obj.type, obj.hide_render, obj.hide_viewport)
