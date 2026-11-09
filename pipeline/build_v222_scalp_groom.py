"""Replace the V217 wire mass with a fitted scalp cap and readable curl layer."""

from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
OUT = ROOT / "production_v222_scalp_groom"
RENDERS = OUT / "renders"
OUTPUT = OUT / "Character_An_scalp_groom_v222.blend"
RENDERS.mkdir(parents=True, exist_ok=True)

head = bpy.data.objects["V216_REFERENCE_FITTED_HEAD"]
matrix = head.matrix_world

# Preserve only the upper scalp. The hairline rises toward the temples and avoids
# covering the baked forehead/eyebrows.
selected_faces = []
selected_vertices = set()
for poly in head.data.polygons:
    points = [matrix @ head.data.vertices[index].co for index in poly.vertices]
    keep = True
    for point in points:
        temple_factor = min(1.0, abs(point.x) / 0.13)
        front_line = 1.720 + 0.024 * temple_factor
        if point.y < -0.045:
            keep = keep and point.z >= front_line
        else:
            keep = keep and point.z >= 1.665
    if keep:
        selected_faces.append(poly)
        selected_vertices.update(poly.vertices)

index_map = {old: new for new, old in enumerate(sorted(selected_vertices))}
vertices = [(matrix @ head.data.vertices[index].co) for index in sorted(selected_vertices)]
faces = [[index_map[index] for index in poly.vertices] for poly in selected_faces]
mesh = bpy.data.meshes.new("V222_SCALP_CAP_DATA")
mesh.from_pydata(vertices, [], faces)
mesh.update()
cap = bpy.data.objects.new("V222_SCALP_CAP", mesh)
bpy.context.scene.collection.objects.link(cap)
for poly in mesh.polygons:
    poly.use_smooth = True

mat = bpy.data.materials.get("V222_HAIR_BASE") or bpy.data.materials.new("V222_HAIR_BASE")
mat.use_nodes = True
nodes = mat.node_tree.nodes
links = mat.node_tree.links
bsdf = nodes.get("Principled BSDF")
bsdf.inputs["Base Color"].default_value = (0.006, 0.003, 0.002, 1.0)
bsdf.inputs["Roughness"].default_value = 0.62
noise = nodes.new("ShaderNodeTexNoise")
noise.name = "V222_SCALP_MICRO"
noise.inputs["Scale"].default_value = 115.0
noise.inputs["Detail"].default_value = 2.0
bump = nodes.new("ShaderNodeBump")
bump.name = "V222_SCALP_BUMP"
bump.inputs["Strength"].default_value = 0.18
bump.inputs["Distance"].default_value = 0.0015
links.new(noise.outputs["Fac"], bump.inputs["Height"])
links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
mesh.materials.append(mat)

solidify = cap.modifiers.new("V222_SCALP_THICKNESS", "SOLIDIFY")
solidify.thickness = 0.0035
solidify.offset = 1.0
subsurf = cap.modifiers.new("V222_SCALP_SMOOTH", "SUBSURF")
subsurf.levels = 1
subsurf.render_levels = 1

# Reject the high-density short fiber mass; retain the larger authored ringlets as
# the readable curl layer and darken/thin them to sit on the scalp foundation.
tight = bpy.data.objects.get("V217_TIGHT_CURL_GROOM")
if tight:
    tight.hide_render = True
    tight.hide_viewport = True
clusters = bpy.data.objects.get("V217_CURL_CLUSTERS")
if clusters:
    clusters.hide_render = False
    clusters.hide_viewport = False
    clusters.data.bevel_depth = 0.00072
    clusters.data.bevel_resolution = 3
    clusters.data.materials.clear()
    clusters.data.materials.append(mat)

camera = bpy.data.objects["V219_CAMERA"]
camera.data.lens = 92.0


def point_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


scene = bpy.context.scene
scene.camera = camera
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 900
scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
target = Vector((0.0, -0.01, 1.61))
views = {
    "front": Vector((0.0, -1.14, 1.61)),
    "left_three_quarter": Vector((-0.72, -0.78, 1.63)),
    "left_profile": Vector((-1.14, 0.0, 1.61)),
}
for name, location in views.items():
    camera.location = location
    point_at(camera, target)
    scene.render.filepath = str(RENDERS / f"v222_{name}.png")
    bpy.ops.render.render(write_still=True)

scene["V222_STATUS"] = "FITTED_SCALP_READABLE_CURL_CANDIDATE"
scene["V222_SCALP_FACES"] = len(faces)
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
print({"status": "ok", "output": str(OUTPUT), "scalp_faces": len(faces), "renders": [str(RENDERS / f"v222_{name}.png") for name in views]})
