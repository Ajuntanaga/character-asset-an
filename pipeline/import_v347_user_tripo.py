"""Preserve the current build and import the user's Tripo mesh into a review scene."""
import bpy
import json
import numpy as np
from pathlib import Path
from mathutils import Matrix, Vector

ROOT = Path('/home/ajuntanaga/Projects/Blender/Character Asset_An')
OUT = ROOT / 'production_v347_user_tripo_intake'
OUT.mkdir(exist_ok=True)
if bpy.data.scenes.get('V347_TRIPO_REVIEW'):
    raise RuntimeError('V347 review already exists; inspect it instead of duplicating the import')
previous_scene = bpy.context.scene
previous_file = bpy.data.filepath
scene = bpy.data.scenes.new('V347_TRIPO_REVIEW')
bpy.context.window.scene = scene
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=str(ROOT / 'third_party/tripo_user_d1b7f249/character_decoded.glb'))
objects = list(set(bpy.data.objects) - before)
meshes = [o for o in objects if o.type == 'MESH']
if len(meshes) != 1:
    raise RuntimeError(f'Expected one source mesh, got {len(meshes)}')
obj = meshes[0]
obj.name = 'V347_TRIPO_CHARACTER_DENSE'
# The supplied file uses Z for height and X for depth, unlike conventional glTF.
# Undo the glTF import axis convention and orient the height along Blender Z.
axis = Matrix(((0, 0, -1, 0), (1, 0, 0, 0), (0, -1, 0, 0), (0, 0, 0, 1)))
obj.data.transform(axis @ obj.matrix_world)
obj.matrix_world = Matrix.Identity(4)
xyz = np.empty(len(obj.data.vertices) * 3, dtype=np.float32)
obj.data.vertices.foreach_get('co', xyz)
xyz = xyz.reshape((-1, 3))
lo, hi = xyz.min(axis=0), xyz.max(axis=0)
scale = 1.8 / float(hi[2] - lo[2])
xyz[:, 0] -= (hi[0] + lo[0]) / 2
xyz[:, 1] -= (hi[1] + lo[1]) / 2
xyz[:, 2] -= lo[2]
xyz *= scale
obj.data.vertices.foreach_set('co', xyz.ravel())
for polygon in obj.data.polygons:
    polygon.use_smooth = True
obj.data.update()
obj['source_file'] = '/home/ajuntanaga/Downloads/tripo_model_d1b7f249-d40b-4b1f-843d-2d35c6ac59b8_meshopt.glb'
obj['source_status'] = 'User supplied; static dense mesh; no original skin or animation'
obj['rig_status'] = 'UNRIGGED_SOURCE'
obj['reference_height_m'] = 1.8

world = bpy.data.worlds.new('V347_STUDIO_WORLD')
world.use_nodes = True
world.node_tree.nodes['Background'].inputs['Color'].default_value = (.20, .23, .28, 1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value = .35
scene.world = world

def area(name, location, energy, size, color):
    data = bpy.data.lights.new(name, 'AREA')
    data.energy, data.shape, data.size, data.color = energy, 'DISK', size, color
    light = bpy.data.objects.new(name, data)
    scene.collection.objects.link(light)
    light.location = location
    light.rotation_euler = (Vector((0, 0, 1.0)) - light.location).to_track_quat('-Z', 'Y').to_euler()

area('V347_KEY', (-2.5, -3.0, 3.8), 450, 3.0, (1.0, .91, .82))
area('V347_FILL', (2.5, -1.5, 2.4), 230, 2.5, (.78, .87, 1.0))
area('V347_RIM', (0, 2.0, 3.0), 500, 2.0, (.87, .93, 1.0))
bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, -.005))
floor = bpy.context.object
floor.name = 'V347_STUDIO_FLOOR'
material = bpy.data.materials.new('V347_NEUTRAL_FLOOR')
material.diffuse_color = (.075, .085, .10, 1)
material.use_nodes = True
bsdf = material.node_tree.nodes.get('Principled BSDF')
bsdf.inputs['Base Color'].default_value = (.075, .085, .10, 1)
bsdf.inputs['Roughness'].default_value = .82
floor.data.materials.append(material)
camera_data = bpy.data.cameras.new('V347_CAMERA')
camera = bpy.data.objects.new('V347_CAMERA', camera_data)
scene.collection.objects.link(camera)
camera.location = (0, -4.1, 1.0)
camera.rotation_euler = (Vector((0, 0, .94)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
camera_data.lens = 60
scene.camera = camera
scene.render.engine = 'CYCLES'
scene.cycles.samples = 48
scene.cycles.use_denoising = True
scene.render.resolution_x, scene.render.resolution_y = 1000, 1400
scene.render.resolution_percentage = 100
scene.view_settings.view_transform = 'AgX'
scene.render.image_settings.file_format = 'PNG'
scene.render.film_transparent = False
scene['source_scene'] = previous_scene.name
scene['quality_status'] = 'Source intake; not yet assessed for animation or likeness'
report = {
    'source': obj['source_file'], 'previous_checkpoint': previous_file,
    'previous_scene': previous_scene.name, 'review_scene': scene.name,
    'object': obj.name, 'vertices': len(obj.data.vertices),
    'polygons': len(obj.data.polygons), 'uv_layers': [uv.name for uv in obj.data.uv_layers],
    'bounds_m': [xyz.min(axis=0).tolist(), xyz.max(axis=0).tolist()],
    'height_scale': scale, 'skin': False, 'animation': False,
    'images': [{'name': n.image.name, 'size': list(n.image.size)}
               for m in obj.data.materials for n in m.node_tree.nodes
               if n.type == 'TEX_IMAGE' and n.image],
    'head_depth_extents': {},
}
for z in (1.55, 1.65, 1.72):
    points = xyz[np.abs(xyz[:, 2] - z) < .015]
    report['head_depth_extents'][str(z)] = [points.min(axis=0).tolist(), points.max(axis=0).tolist()]
(OUT / 'intake.json').write_text(json.dumps(report, indent=2))
bpy.ops.object.select_all(action='DESELECT')
obj.select_set(True)
bpy.context.view_layer.objects.active = obj
for screen in bpy.data.screens:
    for area_ui in screen.areas:
        if area_ui.type == 'VIEW_3D':
            area_ui.spaces.active.shading.type = 'MATERIAL'
            area_ui.spaces.active.overlay.show_overlays = False
            area_ui.spaces.active.region_3d.view_perspective = 'CAMERA'
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'Character_An_user_Tripo_v347.blend'))
print(json.dumps(report))
