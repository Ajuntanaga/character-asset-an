import bpy
from mathutils import Vector


keywords = ("hand", "finger", "thumb", "index", "middle", "ring", "pinky", "palm", "nail", "contact", "pinch", "pick")
for obj in sorted(bpy.context.scene.objects, key=lambda item: item.name):
    if obj.hide_render or obj.type not in {"MESH", "CURVE", "EMPTY"}:
        continue
    if any(word in obj.name.lower() for word in keywords):
        if obj.type == "EMPTY":
            print("HAND_OBJECT", obj.name, obj.type, tuple(round(value, 6) for value in obj.matrix_world.translation), "EMPTY")
            continue
        corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
        minimum = tuple(round(min(point[index] for point in corners), 5) for index in range(3))
        maximum = tuple(round(max(point[index] for point in corners), 5) for index in range(3))
        print("HAND_OBJECT", obj.name, obj.type, minimum, maximum, [slot.material.name if slot.material else None for slot in obj.material_slots])

for obj in sorted(bpy.data.objects, key=lambda item: item.name):
    if obj.type == "CAMERA" and any(word in obj.name.lower() for word in ("pick", "fret", "hand", "macro")):
        print("HAND_CAMERA", obj.name)
