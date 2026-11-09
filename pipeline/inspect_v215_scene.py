import bpy

head = bpy.data.objects["V215_FACEBUILDER_IDENTITY_HEAD"]
print({
    "head_bounds": [tuple(round(v, 5) for v in corner) for corner in head.bound_box],
    "head_vertices": len(head.data.vertices),
    "head_polygons": len(head.data.polygons),
    "cameras": [
        {
            "name": obj.name,
            "location": tuple(round(v, 5) for v in obj.location),
            "rotation": tuple(round(v, 5) for v in obj.rotation_euler),
            "lens": obj.data.lens,
            "background": obj.data.background_images[0].image.filepath
            if obj.data.background_images and obj.data.background_images[0].image
            else None,
        }
        for obj in bpy.data.objects
        if obj.type == "CAMERA"
    ],
})
