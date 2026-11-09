import bpy
from mathutils import Vector

for name in ("V212_EYE_L", "V212_EYE_R"):
    obj = bpy.data.objects[name]
    corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    print(name, {
        "matrix_translation": tuple(round(v, 6) for v in obj.matrix_world.translation),
        "bbox_min": tuple(round(min(v[i] for v in corners), 6) for i in range(3)),
        "bbox_max": tuple(round(max(v[i] for v in corners), 6) for i in range(3)),
        "data_center": tuple(round(sum(v.co[i] for v in obj.data.vertices) / len(obj.data.vertices), 6) for i in range(3)),
    })
