"""Render isolated orthographic views of the V215 fitted FaceBuilder head."""

from pathlib import Path
from mathutils import Vector

import bpy


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
OUT = ROOT / "production_v215_facebuilder_identity" / "renders"
OUT.mkdir(parents=True, exist_ok=True)
head = bpy.data.objects["V215_FACEBUILDER_IDENTITY_HEAD"]

for obj in bpy.context.scene.objects:
    obj.hide_render = obj != head
head.hide_render = False

material = bpy.data.materials.get("V215_DIAGNOSTIC_SKIN") or bpy.data.materials.new(
    "V215_DIAGNOSTIC_SKIN"
)
material.diffuse_color = (0.34, 0.13, 0.065, 1.0)
material.use_nodes = True
principled = material.node_tree.nodes.get("Principled BSDF")
principled.inputs["Base Color"].default_value = (0.34, 0.13, 0.065, 1.0)
principled.inputs["Roughness"].default_value = 0.47
principled.inputs["Specular IOR Level"].default_value = 0.28
head.data.materials.clear()
head.data.materials.append(material)
for polygon in head.data.polygons:
    polygon.use_smooth = True

center = head.matrix_world @ Vector((0.0, -0.12, -0.20))


def point_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


camera_data = bpy.data.cameras.new("V215_DIAGNOSTIC_CAMERA_DATA")
camera_data.type = "ORTHO"
camera_data.ortho_scale = 3.75
camera = bpy.data.objects.new("V215_DIAGNOSTIC_CAMERA", camera_data)
bpy.context.scene.collection.objects.link(camera)

key_data = bpy.data.lights.new("V215_KEY_DATA", "AREA")
key_data.energy = 650.0
key_data.shape = "DISK"
key_data.size = 4.0
key = bpy.data.objects.new("V215_KEY", key_data)
bpy.context.scene.collection.objects.link(key)
key.location = (-3.5, -4.0, 4.2)
point_at(key, center)
key.hide_render = False

fill_data = bpy.data.lights.new("V215_FILL_DATA", "AREA")
fill_data.energy = 300.0
fill_data.size = 3.0
fill = bpy.data.objects.new("V215_FILL", fill_data)
bpy.context.scene.collection.objects.link(fill)
fill.location = (3.0, -2.2, 1.2)
point_at(fill, center)
fill.hide_render = False

rim_data = bpy.data.lights.new("V215_RIM_DATA", "AREA")
rim_data.energy = 500.0
rim_data.size = 2.5
rim = bpy.data.objects.new("V215_RIM", rim_data)
bpy.context.scene.collection.objects.link(rim)
rim.location = (2.5, 2.2, 3.5)
point_at(rim, center)
rim.hide_render = False

scene = bpy.context.scene
scene.camera = camera
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 768
scene.render.resolution_y = 768
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.film_transparent = False
scene.world.color = (0.025, 0.025, 0.025)

views = {
    "front": Vector((0.0, -7.0, -0.2)),
    "left_three_quarter": Vector((-4.5, -4.5, -0.2)),
    "left_profile": Vector((-7.0, 0.0, -0.2)),
}
for name, location in views.items():
    camera.location = location
    point_at(camera, center)
    scene.render.filepath = str(OUT / f"v215_{name}.png")
    bpy.ops.render.render(write_still=True)

bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
print({"status": "ok", "renders": [str(OUT / f"v215_{name}.png") for name in views]})
