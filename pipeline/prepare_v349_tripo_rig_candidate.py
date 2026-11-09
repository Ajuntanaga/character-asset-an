"""Restore extracted UVs and prepare the strongest figure for CloudRig fitting."""
import bpy
import json
import numpy as np
from pathlib import Path
from mathutils import Matrix, Vector

ROOT = Path('/home/ajuntanaga/Projects/Blender/Character Asset_An')
OUT = ROOT / 'production_v349_tripo_rig_candidate'
OUT.mkdir(exist_ok=True)
if bpy.data.scenes.get('V349_TRIPO_RIG_CANDIDATE'):
    raise RuntimeError('V349 already exists; inspect instead of duplicating')

source = bpy.data.objects['V347_TRIPO_CHARACTER_DENSE'].data
xyz = np.empty(len(source.vertices) * 3, dtype=np.float32)
source.vertices.foreach_get('co', xyz)
xyz = xyz.reshape((-1, 3))
indices = np.empty(len(source.loops), dtype=np.int32)
source.loops.foreach_get('vertex_index', indices)
triangles = indices.reshape((-1, 3))
source_uv = np.empty(len(source.loops) * 2, dtype=np.float32)
source.uv_layers.active.data.foreach_get('uv', source_uv)
source_uv = source_uv.reshape((-1, 3, 2))
checks = []
boundaries = (0, .48, .84, 1.323, 1.81)
for i, (lower, upper) in enumerate(zip(boundaries[:-1], boundaries[1:]), 1):
    mask = (xyz[:, 2] >= lower) & (xyz[:, 2] < upper)
    faces = np.all(mask[triangles], axis=1)
    obj = bpy.data.objects[f'V348_TRIPO_FIGURE_{i:02d}']
    expected = np.ascontiguousarray(source_uv[faces].ravel())
    layer = obj.data.uv_layers.active
    assert len(layer.data) * 2 == expected.size
    layer.data.foreach_set('uv', expected)
    obj.data.update()
    actual = np.empty_like(expected)
    layer.data.foreach_get('uv', actual)
    error = float(np.max(np.abs(actual - expected)))
    assert error == 0, f'UV restoration failed: {obj.name}'
    checks.append({'object': obj.name, 'max_uv_error': error})

lineup = bpy.data.scenes['V348_TRIPO_FIGURES']
scene = bpy.data.scenes.new('V349_TRIPO_RIG_CANDIDATE')
bpy.context.window.scene = scene
scene.world = lineup.world
for original in lineup.objects:
    if original.type in {'CAMERA', 'LIGHT'} or original.name.startswith('V347_STUDIO_FLOOR'):
        copy = original.copy()
        copy.data = original.data.copy()
        scene.collection.objects.link(copy)
        if copy.type == 'CAMERA':
            scene.camera = copy

original = bpy.data.objects['V348_TRIPO_FIGURE_04']
character = original.copy()
character.data = original.data.copy()
character.name = 'V349_TRIPO_CHARACTER_SOURCE'
character.data.name = 'V349_TRIPO_CHARACTER_SOURCE_MESH'
character.location = (0, 0, 0)
character.data.transform(Matrix.Rotation(np.pi, 4, 'Z'))
character.data.update()
character['source_figure'] = 4
character['rig_status'] = 'UV_REPAIRED_UNBOUND_SOURCE'
scene.collection.objects.link(character)

scene.camera.name = 'V349_CAMERA'
scene.camera.location = (0, -4.1, 1.0)
scene.camera.rotation_euler = (Vector((0, 0, .94)) - scene.camera.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera.data.lens = 60
scene.render.engine = 'CYCLES'
scene.cycles.samples = 48
scene.cycles.use_denoising = True
scene.render.resolution_x, scene.render.resolution_y = 1000, 1400
scene.render.resolution_percentage = 100
scene.view_settings.view_transform = 'AgX'
bpy.ops.object.select_all(action='DESELECT')
character.select_set(True)
bpy.context.view_layer.objects.active = character
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces.active.region_3d.view_perspective = 'CAMERA'
            area.spaces.active.shading.type = 'MATERIAL'

report = {'source_figure': 4, 'uv_restoration': checks,
          'vertices': len(character.data.vertices), 'triangles': len(character.data.polygons),
          'rig': 'CloudRig Sintel; generated separately, fitting pending',
          'status': 'Textured high-poly candidate; not animation ready'}
path = OUT / 'Character_An_Tripo_candidate_v349.blend'
bpy.data.libraries.write(str(path), {scene}, fake_user=True, compress=True)
(OUT / 'candidate.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report))
