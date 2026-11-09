import bpy

body = bpy.data.objects.get("V212_BODY_IDENTITY")
landmarks = {
    name: tuple(round(v, 6) for v in bpy.data.objects[name].matrix_world.translation)
    for name in (
        "LM_V212_CROWN",
        "LM_V212_BROW",
        "LM_V212_EYE_L",
        "LM_V212_EYE_R",
        "LM_V212_NOSE_TIP",
        "LM_V212_MOUTH",
        "LM_V212_CHIN",
    )
    if name in bpy.data.objects
}
print({
    "body": body.name if body else None,
    "body_matrix": [tuple(round(v, 6) for v in row) for row in body.matrix_world] if body else None,
    "landmarks": landmarks,
})
