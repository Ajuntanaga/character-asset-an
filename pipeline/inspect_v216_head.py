import bpy

obj = bpy.data.objects["V216_REFERENCE_FITTED_HEAD"]
depsgraph = bpy.context.evaluated_depsgraph_get()
evaluated = obj.evaluated_get(depsgraph)
corners = [evaluated.matrix_world @ __import__("mathutils").Vector(corner) for corner in evaluated.bound_box]
print({
    "hide_render": obj.hide_render,
    "hide_viewport": obj.hide_viewport,
    "parent": obj.parent.name if obj.parent else None,
    "parent_type": obj.parent_type,
    "parent_bone": obj.parent_bone,
    "matrix_world": [tuple(round(v, 6) for v in row) for row in evaluated.matrix_world],
    "bbox_min": tuple(round(min(v[i] for v in corners), 6) for i in range(3)),
    "bbox_max": tuple(round(max(v[i] for v in corners), 6) for i in range(3)),
    "materials": [m.name if m else None for m in obj.data.materials],
})
