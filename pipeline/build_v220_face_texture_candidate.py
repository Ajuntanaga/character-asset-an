"""Bake the fitted FaceBuilder reference views and render a V220 identity candidate."""

from pathlib import Path

import bpy
from mathutils import Vector

from keentools.facebuilder.settings import fb_settings
from keentools.utils.materials import bake_tex, show_texture_in_mat, assign_material_to_object


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
OUT = ROOT / "production_v220_face_texture"
RENDERS = OUT / "renders"
OUTPUT = OUT / "Character_An_face_texture_v220.blend"
RENDERS.mkdir(parents=True, exist_ok=True)

settings = fb_settings()
if len(settings.heads) != 1:
    raise RuntimeError(f"Expected one FaceBuilder head, found {len(settings.heads)}")

head = settings.get_head(0)
if head.headobj is None or len(head.cameras) != 3:
    raise RuntimeError("V220 requires the fitted three-camera FaceBuilder head")

settings.tex_width = 4096
settings.tex_height = 4096
settings.tex_equalize_brightness = True
settings.tex_equalize_colour = True
settings.tex_fill_gaps = True
settings.tex_auto_preview = True

status = bake_tex(0, head.preview_texture_name())
if not status.success:
    raise RuntimeError(status.error_message)

material = show_texture_in_mat(head.preview_texture_name(), head.preview_material_name())
assign_material_to_object(head.headobj, material)

# Remove diagnostic skin bump from the baked head material if inherited.
bsdf = material.node_tree.nodes.get("Principled BSDF") if material.use_nodes else None
if bsdf:
    bsdf.inputs["Roughness"].default_value = 0.48
    bsdf.inputs["Specular IOR Level"].default_value = 0.28

# Use the existing portrait rig, but render an identity close-up rather than a distant full body.
camera = bpy.data.objects.get("V219_CAMERA")
if camera is None:
    raise RuntimeError("V219 camera missing")
camera.data.lens = 85.0


def point_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


scene = bpy.context.scene
scene.camera = camera
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 900
scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.film_transparent = False
scene.world.color = (0.018, 0.018, 0.018)

target = Vector((0.0, -0.01, 1.60))
views = {
    "front": Vector((0.0, -1.14, 1.60)),
    "left_three_quarter": Vector((-0.72, -0.78, 1.62)),
    "left_profile": Vector((-1.14, 0.0, 1.60)),
}
for name, location in views.items():
    camera.location = location
    point_at(camera, target)
    scene.render.filepath = str(RENDERS / f"v220_{name}.png")
    bpy.ops.render.render(write_still=True)

scene["V220_STATUS"] = "FACEBUILDER_REFERENCE_TEXTURE_CANDIDATE"
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
print({
    "status": "ok",
    "output": str(OUTPUT),
    "texture": head.preview_texture_name(),
    "resolution": [settings.tex_width, settings.tex_height],
    "renders": [str(RENDERS / f"v220_{name}.png") for name in views],
})
