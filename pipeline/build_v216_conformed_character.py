"""Conform the fitted V215 head to the V212/V214 body and rig."""

from pathlib import Path

import bmesh
import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
STAGE = ROOT / "production_v216_conformed_character"
OUTPUT = STAGE / "Character_An_conformed_v216.blend"
RENDER_DIR = STAGE / "renders"
STAGE.mkdir(parents=True, exist_ok=True)
RENDER_DIR.mkdir(parents=True, exist_ok=True)

head = bpy.data.objects["V215_FACEBUILDER_IDENTITY_HEAD"]
body = bpy.data.objects["V212_BODY_IDENTITY"]
rig = bpy.data.objects.get("V214_CHARACTER_RIG")

# Derived from the authoritative V212 landmark targets:
# crown z=1.800, nose tip y=-0.153, collar-safe neck overlap z=1.369..1.405.
scale = 0.136
head.scale = (scale, scale, scale)
head.location = (0.0016, 0.0190, 1.6145)
head.rotation_euler = (0.0, 0.0, 0.0)
head.name = "V216_REFERENCE_FITTED_HEAD"

# Remove the obsolete base-mesh head while retaining a short neck stub.  The
# fitted head overlaps the stub by ~36 mm; the final shirt collar conceals the
# seam while both pieces are driven by the same head/neck rig chain.
cut_z = 1.405
mesh = body.data
bm = bmesh.new()
bm.from_mesh(mesh)
delete = [
    vert
    for vert in bm.verts
    if (body.matrix_world @ vert.co).z > cut_z
    and abs((body.matrix_world @ vert.co).x) < 0.15
]
bmesh.ops.delete(bm, geom=delete, context="VERTS")
bm.to_mesh(mesh)
bm.free()
mesh.update()
body.name = "V216_BODY_WITH_NECK_STUB"

# Keep the conformation transform in world space for this visual gate.  Bone
# attachment is added only after the head/body seam and eye placement pass;
# direct bone parenting here resets the FaceBuilder object's fitted transform.
head.parent = None

for eye_name in ("V212_EYE_L", "V212_EYE_R"):
    eye = bpy.data.objects.get(eye_name)
    if eye:
        world = eye.matrix_world.copy()
        world.translation = Vector((
            0.043 if eye_name.endswith("_L") else -0.043,
            -0.145,
            1.675,
        ))
        eye.parent = None
        eye.matrix_world = world
        eye.parent = head
        eye.parent_type = "OBJECT"
        eye.matrix_world = world
        eye.hide_render = False

for obj in bpy.context.scene.objects:
    obj.hide_render = obj not in {head, body, bpy.data.objects.get("V212_EYE_L"), bpy.data.objects.get("V212_EYE_R")}

skin = bpy.data.materials.get("V216_SKIN") or bpy.data.materials.new("V216_SKIN")
skin.use_nodes = True
skin.diffuse_color = (0.30, 0.105, 0.045, 1.0)
bsdf = skin.node_tree.nodes.get("Principled BSDF")
bsdf.inputs["Base Color"].default_value = (0.30, 0.105, 0.045, 1.0)
bsdf.inputs["Roughness"].default_value = 0.48
bsdf.inputs["Specular IOR Level"].default_value = 0.25
head.data.materials.clear()
head.data.materials.append(skin)

camera_data = bpy.data.cameras.new("V216_CAMERA_DATA")
camera_data.lens = 72.0
camera = bpy.data.objects.new("V216_CAMERA", camera_data)
bpy.context.scene.collection.objects.link(camera)
camera.hide_render = False


def point_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


target = Vector((0.0, -0.015, 1.575))
key_data = bpy.data.lights.new("V216_KEY_DATA", "AREA")
key_data.energy = 500.0
key_data.size = 2.0
key = bpy.data.objects.new("V216_KEY", key_data)
bpy.context.scene.collection.objects.link(key)
key.location = (-1.4, -2.2, 2.8)
point_at(key, target)
key.hide_render = False

fill_data = bpy.data.lights.new("V216_FILL_DATA", "AREA")
fill_data.energy = 220.0
fill_data.size = 2.0
fill = bpy.data.objects.new("V216_FILL", fill_data)
bpy.context.scene.collection.objects.link(fill)
fill.location = (1.3, -1.5, 1.8)
point_at(fill, target)
fill.hide_render = False

scene = bpy.context.scene
scene.camera = camera
scene.frame_set(1)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 768
scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.world.color = (0.02, 0.02, 0.02)
views = {
    "front": Vector((0.0, -2.25, 1.62)),
    "left_three_quarter": Vector((-1.25, -1.75, 1.64)),
    "left_profile": Vector((-2.25, 0.0, 1.62)),
}
for name, location in views.items():
    camera.location = location
    point_at(camera, target)
    scene.render.filepath = str(RENDER_DIR / f"v216_{name}.png")
    bpy.ops.render.render(write_still=True)

scene["V216_STATUS"] = "REFERENCE_FITTED_HEAD_CONFORMED_CANDIDATE"
scene["V216_HEAD_SCALE"] = scale
scene["V216_BODY_CUT_Z"] = cut_z
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
print({
    "status": "ok",
    "output": str(OUTPUT),
    "head": head.name,
    "body": body.name,
    "body_vertices": len(body.data.vertices),
    "head_vertices": len(head.data.vertices),
    "renders": [str(RENDER_DIR / f"v216_{name}.png") for name in views],
})
