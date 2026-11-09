import bpy
from mathutils import Vector


for name in ("V163_BODY_FAILED_PICKING_HAND_MASKED", "V131_CLEAN_CONNECTED_SHORT_CURL_HAIR"):
    obj = bpy.data.objects.get(name)
    print("INSPECT_OBJECT", name, obj.type if obj else None)
    if obj:
        print("  BOUNDS", [tuple(round(v, 4) for v in corner) for corner in obj.bound_box])
        print("  LOCATION", tuple(round(v, 4) for v in obj.location))
        print("  MATERIALS", [slot.material.name if slot.material else None for slot in obj.material_slots])
        if obj.type == "MESH":
            print("  COUNTS", len(obj.data.vertices), len(obj.data.polygons))

for obj in sorted(bpy.data.objects, key=lambda item: item.name):
    if obj.type == "CAMERA" and (obj.name.startswith("V95") or obj.name.startswith("V151")):
        print("INSPECT_CAMERA", obj.name, tuple(round(v, 4) for v in obj.location), tuple(round(v, 4) for v in obj.rotation_euler))

for material in sorted(bpy.data.materials, key=lambda item: item.name):
    if any(word in material.name.lower() for word in ("skin", "hair", "eye", "beard")):
        print("INSPECT_MATERIAL", material.name, tuple(round(v, 4) for v in material.diffuse_color))

print("INSPECT_VISIBLE_HEAD_REGION")
for obj in sorted(bpy.context.scene.objects, key=lambda item: item.name):
    if obj.hide_render or obj.type not in {"MESH", "CURVE"}:
        continue
    corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    minimum = tuple(min(point[index] for point in corners) for index in range(3))
    maximum = tuple(max(point[index] for point in corners) for index in range(3))
    if maximum[2] > 1.5 and minimum[0] > -0.32 and maximum[0] < 0.32 and minimum[1] > -0.35 and maximum[1] < 0.35:
        print(
            "  HEAD_OBJECT",
            obj.name,
            obj.type,
            tuple(round(v, 4) for v in minimum),
            tuple(round(v, 4) for v in maximum),
        )
