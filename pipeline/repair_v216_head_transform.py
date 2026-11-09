import bpy
from mathutils import Matrix, Vector

head = bpy.data.objects["V216_REFERENCE_FITTED_HEAD"]
eyes = [bpy.data.objects.get(name) for name in ("V212_EYE_L", "V212_EYE_R")]
eye_world = {eye.name: eye.matrix_world.copy() for eye in eyes if eye}
for eye in eyes:
    if eye:
        eye.parent = None
        eye.matrix_world = eye_world[eye.name]

head.parent = None
head.parent_type = "OBJECT"
head.parent_bone = ""
head.matrix_world = Matrix.Translation(Vector((0.0016, 0.0190, 1.6145))) @ Matrix.Diagonal((0.136, 0.136, 0.136, 1.0))

for eye in eyes:
    if eye:
        world = eye_world[eye.name]
        eye.parent = head
        eye.matrix_world = world

bpy.context.scene["V216_RIG_ATTACHMENT"] = "PENDING_AFTER_VISUAL_CONFORMATION_GATE"
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
print({"head_matrix": [tuple(round(v, 6) for v in row) for row in head.matrix_world]})
