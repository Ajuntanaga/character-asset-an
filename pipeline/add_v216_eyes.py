import bpy
from mathutils import Vector


def material(name, color, roughness=0.35, metallic=0.0):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat


for obj in list(bpy.data.objects):
    if obj.name in {"V212_EYE_L", "V212_EYE_R"} or obj.name.startswith(
        ("V216_EYE_", "V216_IRIS_", "V216_PUPIL_")
    ):
        bpy.data.objects.remove(obj, do_unlink=True)

sclera = material("V216_SCLERA", (0.38, 0.28, 0.21, 1.0), 0.32)
iris = material("V216_IRIS", (0.055, 0.020, 0.006, 1.0), 0.34)
pupil = material("V216_PUPIL", (0.003, 0.002, 0.001, 1.0), 0.2)

for side, x in (("L", 0.043), ("R", -0.043)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=0.0125, location=(x, -0.100, 1.659))
    eye = bpy.context.object
    eye.name = f"V216_EYE_{side}"
    eye.data.materials.append(sclera)

    for suffix, radius, y, mat in (
        ("IRIS", 0.0052, -0.1127, iris),
        ("PUPIL", 0.00225, -0.1131, pupil),
    ):
        bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=radius, depth=0.0007, location=(x, y, 1.659), rotation=(1.57079632679, 0.0, 0.0))
        disk = bpy.context.object
        disk.name = f"V216_{suffix}_{side}"
        disk.data.materials.append(mat)

bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
print({"status": "ok", "eyes": [obj.name for obj in bpy.data.objects if obj.name.startswith("V216_EYE_")]})
