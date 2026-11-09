import bpy

root = bpy.data.objects["V206_GUITAR_ROOT"]


def descends_from(obj, ancestor):
    current = obj.parent
    for _ in range(32):
        if current is None:
            return False
        if current == ancestor:
            return True
        current = current.parent
    raise RuntimeError(f"Parent chain exceeds 32 levels: {obj.name}")


members = [obj for obj in bpy.data.objects if obj == root or descends_from(obj, root)]
print("ROOT_TRANSFORM", tuple(root.location), tuple(root.rotation_euler), tuple(root.scale))
print("GUITAR_MEMBER_COUNT", len(members))
for obj in sorted(members, key=lambda item: item.name):
    print("GUITAR_MEMBER", obj.name, obj.type, obj.parent.name if obj.parent else None)
