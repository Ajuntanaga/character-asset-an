import bpy
from mathutils import Vector


keywords = ("jacket", "shirt", "trouser", "boot", "sock", "pocket", "button", "pen", "cuff", "collar", "body")
for obj in sorted(bpy.context.scene.objects, key=lambda item: item.name):
    if obj.hide_render or obj.type not in {"MESH", "CURVE"}:
        continue
    if any(word in obj.name.lower() for word in keywords):
        corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
        minimum = tuple(round(min(point[index] for point in corners), 4) for index in range(3))
        maximum = tuple(round(max(point[index] for point in corners), 4) for index in range(3))
        materials = [slot.material.name if slot.material else None for slot in obj.material_slots]
        print("WARDROBE", obj.name, obj.type, minimum, maximum, materials)
