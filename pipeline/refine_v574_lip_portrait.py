"""Fit the original front portrait to the separate lip patch in its rest pose."""
import json
from pathlib import Path

import bpy
import numpy as np
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform


def build(output):
    root = Path(__file__).resolve().parents[1]
    source = root / 'references/derived/photoreal_facebuilder_v1'
    fitted = json.loads((source / 'fitted_cameras_v326.json').read_text())['front']
    lips = bpy.data.objects['V363_LIPS']
    mesh = lips.data
    assert len(mesh.vertices) == 960 and len(mesh.materials) == 1
    assert not mesh.uv_layers.get('V574_LipFrontUV')
    donor = bpy.data.objects['V376_FACE_PHOTO_DONOR']
    raw = [donor.matrix_world @ v.co for v in donor.data.shape_keys.key_blocks['Basis'].data]
    source_z = [-1.72, -.85, -.30, .0515203, .33, .52, .80, .94, 1.3065]
    target_z = [1.435, 1.521, 1.571, 1.609121, 1.645, 1.670, 1.709, 1.732, 1.795]
    mapped = [Vector((p.x * .123 + .0016, p.y * .121 + .00802,
                      float(np.interp(p.z, source_z, target_z)))) for p in raw]
    donor.data.calc_loop_triangles()
    triangles = [tuple(t.vertices) for t in donor.data.loop_triangles]
    tree = BVHTree.FromPolygons(mapped, triangles, all_triangles=True)
    uv_vertex = np.zeros((len(mesh.vertices), 2), np.float32)
    projection = bpy.data.scenes.new('V574_TEMP_PROJECTION')
    camera_data = bpy.data.cameras.new('V574_TEMP_PROJECTION')
    camera = bpy.data.objects.new('V574_TEMP_PROJECTION', camera_data)
    projection.collection.objects.link(camera)
    nearest_count = 0
    try:
        for key, value in fitted['camera'].items():
            setattr(camera_data, key, value)
        camera.matrix_world = Matrix(fitted['matrix'])
        projection.render.resolution_x, projection.render.resolution_y = fitted['size']
        projection.render.pixel_aspect_x = projection.render.pixel_aspect_y = 1.
        projection.view_layers[0].update()
        for i, vertex in enumerate(mesh.shape_keys.key_blocks['Basis'].data):
            p = lips.matrix_world @ vertex.co
            hit, _, index, _ = tree.ray_cast(Vector((p.x, -.4, p.z)), Vector((0, 1, 0)))
            if hit is None:
                hit, _, index, _ = tree.find_nearest(p)
                nearest_count += 1
            assert hit is not None, i
            triangle = triangles[index]
            point = barycentric_transform(hit, *[mapped[j] for j in triangle],
                                          *[raw[j] for j in triangle])
            uv = world_to_camera_view(projection, camera, point)
            assert uv.z > 0 and 0 < uv.x < 1 and 0 < uv.y < 1, (i, tuple(uv))
            uv_vertex[i] = uv.xy
    finally:
        bpy.data.objects.remove(camera, do_unlink=True)
        bpy.data.cameras.remove(camera_data)
        bpy.data.scenes.remove(projection)
    previous_uv = mesh.uv_layers.active_index
    layer = mesh.uv_layers.new(name='V574_LipFrontUV')
    for loop in mesh.loops:
        layer.data[loop.index].uv = uv_vertex[loop.vertex_index]
    mesh.uv_layers.active_index = previous_uv
    attribute = mesh.attributes.new('V574_LipPortraitWeight', 'FLOAT', 'POINT')
    for i, value in enumerate(attribute.data):
        row = i // 96
        value.value = 1. if row <= 7 else .5 if row == 8 else 0.
    material = mesh.materials[0].copy()
    material.name = 'V574_LIPS_FRONT_PORTRAIT'
    nodes, links = material.node_tree.nodes, material.node_tree.links
    shader = nodes['Principled BSDF']
    previous_color = shader.inputs['Base Color'].links[0].from_socket
    uv_node = nodes.new('ShaderNodeUVMap')
    uv_node.uv_map = layer.name
    image = bpy.data.images.load(str(source / fitted['image']), check_existing=True)
    image.pack()
    texture = nodes.new('ShaderNodeTexImage')
    texture.name = 'V574_FrontPortrait'
    texture.image = image
    texture.interpolation = 'Linear'
    texture.extension = 'EXTEND'
    links.new(uv_node.outputs['UV'], texture.inputs['Vector'])
    mask = nodes.new('ShaderNodeAttribute')
    mask.attribute_name = attribute.name
    mix = nodes.new('ShaderNodeMixRGB')
    mix.name = 'V574_LipPortraitComposite'
    links.new(mask.outputs['Fac'], mix.inputs[0])
    links.new(previous_color, mix.inputs[1])
    links.new(texture.outputs['Color'], mix.inputs[2])
    links.new(mix.outputs[0], shader.inputs['Base Color'])
    mesh.materials[0] = material
    mesh.update()
    assert len(bpy.data.objects['V357_CLOUDRIG_CONTROLS'].animation_data.drivers) == 1957
    report = {'material': material.name, 'source_image': fitted['image'],
              'projected_vertices': len(uv_vertex), 'nearest_fallbacks': nearest_count,
              'uv_min': uv_vertex.min(axis=0).tolist(), 'uv_max': uv_vertex.max(axis=0).tolist(),
              'geometry_changed': False, 'rig_drivers': 1957,
              'status': 'TRIAL_REQUIRES_NEUTRAL_AND_EXPRESSION_RENDER_REVIEW'}
    (Path(output) / 'lip-portrait-report.json').write_text(json.dumps(report, indent=2))
    return report
