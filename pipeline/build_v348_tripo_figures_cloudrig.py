"""Separate the user's four-figure source and install the free CloudRig toolkit."""
import bpy
import json
import numpy as np
from pathlib import Path
from mathutils import Vector

ROOT = Path('/home/ajuntanaga/Projects/Blender/Character Asset_An')
OUT = ROOT / 'production_v348_tripo_figures_cloudrig'
OUT.mkdir(exist_ok=True)
if bpy.data.scenes.get('V348_TRIPO_FIGURES'):
    raise RuntimeError('V348 already exists; inspect the existing scene')

module = 'bl_ext.user_default.cloudrig'
if module not in bpy.context.preferences.addons:
    result = bpy.ops.extensions.package_install_files(
        filepath=str(ROOT / 'third_party/cloudrig/add-on-cloudrig-v2.2.31.zip'),
        repo='user_default', enable_on_install=True)
    if result != {'FINISHED'} or module not in bpy.context.preferences.addons:
        raise RuntimeError(f'CloudRig installation did not complete: {result}')
    bpy.ops.wm.save_userpref()

source = bpy.data.objects['V347_TRIPO_CHARACTER_DENSE']
mesh = source.data
xyz = np.empty(len(mesh.vertices) * 3, dtype=np.float32)
mesh.vertices.foreach_get('co', xyz)
xyz = xyz.reshape((-1, 3))
loop_verts = np.empty(len(mesh.loops), dtype=np.int32)
mesh.loops.foreach_get('vertex_index', loop_verts)
counts = np.empty(len(mesh.polygons), dtype=np.int32)
mesh.polygons.foreach_get('loop_total', counts)
assert np.all(counts == 3), 'Source must be triangulated'
triangles = loop_verts.reshape((-1, 3))
uvs = {}
for layer in mesh.uv_layers:
    values = np.empty(len(mesh.loops) * 2, dtype=np.float32)
    layer.data.foreach_get('uv', values)
    uvs[layer.name] = values.reshape((-1, 3, 2))

previous_scene = bpy.context.scene
scene = bpy.data.scenes.new('V348_TRIPO_FIGURES')
bpy.context.window.scene = scene
scene.world = previous_scene.world
for obj in previous_scene.objects:
    if obj.type in {'CAMERA', 'LIGHT'} or obj.name == 'V347_STUDIO_FLOOR':
        copy = obj.copy()
        copy.data = obj.data.copy()
        scene.collection.objects.link(copy)
        if copy.type == 'CAMERA':
            scene.camera = copy

figures = []
boundaries = (0, .48, .84, 1.323, 1.81)
for number, (lower, upper) in enumerate(zip(boundaries[:-1], boundaries[1:]), 1):
    mask = (xyz[:, 2] >= lower) & (xyz[:, 2] < upper)
    faces = np.all(mask[triangles], axis=1)
    crossing = np.any(mask[triangles], axis=1) & ~faces
    assert not crossing.any(), f'Figure {number} boundary cuts geometry'
    indices = np.unique(triangles[faces])
    remap = np.full(len(xyz), -1, dtype=np.int32)
    remap[indices] = np.arange(len(indices), dtype=np.int32)
    new_xyz = xyz[indices][:, [2, 1, 0]].copy()
    new_xyz[:, 2] *= -1
    lo, hi = new_xyz.min(axis=0), new_xyz.max(axis=0)
    new_xyz[:, :2] -= (lo[:2] + hi[:2]) / 2
    new_xyz[:, 2] -= lo[2]
    scale = 1.8 / (hi[2] - lo[2])
    new_xyz *= scale
    new_triangles = remap[triangles[faces]]

    data = bpy.data.meshes.new(f'V348_FIGURE_{number:02d}_MESH')
    data.vertices.add(len(indices))
    data.vertices.foreach_set('co', new_xyz.ravel())
    data.loops.add(new_triangles.size)
    data.loops.foreach_set('vertex_index', new_triangles.ravel())
    data.polygons.add(len(new_triangles))
    data.polygons.foreach_set('loop_start', np.arange(0, new_triangles.size, 3, dtype=np.int32))
    data.polygons.foreach_set('loop_total', np.full(len(new_triangles), 3, dtype=np.int32))
    data.polygons.foreach_set('use_smooth', np.ones(len(new_triangles), dtype=bool))
    # Initialize topology before adding UVs; otherwise update replaces them
    # with the new mesh's default triangle coordinates.
    data.update()
    for name, values in uvs.items():
        layer = data.uv_layers.new(name=name)
        layer.data.foreach_set('uv', np.ascontiguousarray(values[faces].ravel()))
    for material in mesh.materials:
        data.materials.append(material)
    data.update()
    obj = bpy.data.objects.new(f'V348_TRIPO_FIGURE_{number:02d}', data)
    scene.collection.objects.link(obj)
    obj.location.x = (number - 2.5) * .90
    obj['source_file'] = source['source_file']
    obj['source_figure'] = number
    obj['rig_status'] = 'UNRIGGED_EXTRACTED_SOURCE'
    figures.append({'name': obj.name, 'vertices': len(data.vertices),
                    'triangles': len(data.polygons), 'scale': float(scale),
                    'bounds': [new_xyz.min(axis=0).tolist(), new_xyz.max(axis=0).tolist()]})

scene.camera.name = 'V348_CAMERA'
scene.camera.location = (0, -7, 1.05)
scene.camera.rotation_euler = (Vector((0, 0, .9)) - scene.camera.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera.data.lens = 60
scene.render.engine = 'CYCLES'
scene.cycles.samples = 32
scene.cycles.use_denoising = True
scene.render.resolution_x, scene.render.resolution_y = 1800, 1200
scene.render.resolution_percentage = 100
scene.view_settings.view_transform = 'AgX'
scene['quality_status'] = 'Four extracted source figures; no animation-ready topology or skin yet'

template_scene = bpy.data.scenes.new('V348_CLOUDRIG_TEMPLATE')
bpy.context.window.scene = template_scene
bpy.ops.object.cloudrig_metarig_add(metarig_name='META-Sintel')
meta = bpy.context.object
meta.name = 'V348_CLOUDRIG_SINTEL_METARIG_TEMPLATE'
meta['purpose'] = 'Free production control-rig template, pending character-specific fitting'
bone_data = [{'name': b.name, 'head': list(b.head_local), 'tail': list(b.tail_local),
              'parent': b.parent.name if b.parent else None} for b in meta.data.bones]
(OUT / 'cloudrig_template_bones.json').write_text(json.dumps(bone_data, indent=2))
bpy.context.window.scene = scene
bpy.ops.object.select_all(action='DESELECT')
obj = bpy.data.objects['V348_TRIPO_FIGURE_04']
obj.select_set(True)
bpy.context.view_layer.objects.active = obj
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces.active.region_3d.view_perspective = 'CAMERA'
            area.spaces.active.shading.type = 'MATERIAL'
            area.spaces.active.overlay.show_overlays = False

report = {'cloudrig_module': module, 'cloudrig_version': '2.2.31',
          'template': meta.name, 'template_bones': len(meta.data.bones),
          'figures': figures, 'cross_boundary_faces': 0,
          'original_preserved': True, 'bound_or_animated': False}
(OUT / 'intake.json').write_text(json.dumps(report, indent=2))
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'Character_An_Tripo_figures_CloudRig_v348.blend'), compress=True)
print(json.dumps(report))
