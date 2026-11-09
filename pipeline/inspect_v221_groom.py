import bpy

for obj in bpy.data.objects:
    if obj.name.startswith("V217_") or obj.name == "V216_REFERENCE_FITTED_HEAD":
        info = {
            "name": obj.name,
            "type": obj.type,
            "location": [round(v, 5) for v in obj.location],
            "dimensions": [round(v, 5) for v in obj.dimensions],
            "scale": [round(v, 5) for v in obj.scale],
        }
        if obj.type == "CURVE":
            info.update({
                "splines": len(obj.data.splines),
                "bevel_depth": obj.data.bevel_depth,
                "bevel_resolution": obj.data.bevel_resolution,
                "resolution_u": obj.data.resolution_u,
            })
        elif obj.type == "MESH":
            info.update({"vertices": len(obj.data.vertices), "polygons": len(obj.data.polygons)})
        print(info)
