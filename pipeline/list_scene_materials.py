import bpy
print("\n".join(sorted(material.name for material in bpy.data.materials if any(token in material.name.upper() for token in ("SKIN", "NAIL", "JACKET", "SHIRT")))))
