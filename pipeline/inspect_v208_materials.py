import bpy
for name in ("V202_BODY", "V208_BODY_WITHOUT_NEUTRAL_ARMS", "V205_FITTED_JACKET_SHELL", "V208_JACKET_TORSO"):
    obj = bpy.data.objects.get(name)
    if obj:
        print(name, [(index, slot.material.name if slot.material else None) for index, slot in enumerate(obj.material_slots)])
        print("indices", sorted(set(p.material_index for p in obj.data.polygons)))
