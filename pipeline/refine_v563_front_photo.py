"""Project the fitted front portrait onto the central face with soft exclusions."""
import json
import math
from pathlib import Path

import bpy
import numpy as np
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform


def smooth(value):
    value = max(0., min(1., value))
    return value * value * (3. - 2. * value)


def build(output):
    root = Path(__file__).resolve().parents[1]
    source = root / 'references/derived/photoreal_facebuilder_v1'
    fitted = json.loads((source / 'fitted_cameras_v326.json').read_text())['front']
    body = bpy.data.objects['V416_BODY_CLEAN_JOIN']
    donor = bpy.data.objects['V376_FACE_PHOTO_DONOR']
    mesh = body.data
    assert 'V563_FrontPhotoUV' not in mesh.uv_layers
    original = bpy.data.materials['V549_REFERENCE_PHOTO_SKIN_BALANCED']
    original_slot = list(mesh.materials).index(original)
    eligible = {v for polygon in mesh.polygons if polygon.material_index == original_slot
                for v in polygon.vertices}
    # Reuse V377/V381 registration. The photo donor and fitted cameras share
    # coordinates; transfer their projection through the same donor triangles.
    raw = [donor.matrix_world @ v.co for v in donor.data.shape_keys.key_blocks['Basis'].data]
    source_z = [-1.72, -.85, -.30, .0515203, .33, .52, .80, .94, 1.3065]
    target_z = [1.435, 1.521, 1.571, 1.609121, 1.645, 1.670, 1.709, 1.732, 1.795]
    mapped = [Vector((p.x * .123 + .0016, p.y * .121 + .00802,
                      float(np.interp(p.z, source_z, target_z)))) for p in raw]
    donor.data.calc_loop_triangles()
    triangles = [tuple(t.vertices) for t in donor.data.loop_triangles]
    tree = BVHTree.FromPolygons(mapped, triangles, all_triangles=True)
    uv_vertex = np.zeros((len(mesh.vertices), 2), np.float32)
    weights = np.zeros(len(mesh.vertices), np.float32)
    counts = {'eligible': 0, 'projected': 0, 'rejected': 0}

    projection_scene = bpy.data.scenes.new('V563_TEMP_PROJECTION')
    camera_data = bpy.data.cameras.new('V563_TEMP_PROJECTION')
    camera = bpy.data.objects.new('V563_TEMP_PROJECTION', camera_data)
    projection_scene.collection.objects.link(camera)
    try:
        for key, value in fitted['camera'].items():
            setattr(camera_data, key, value)
        camera.matrix_world = Matrix(fitted['matrix'])
        projection_scene.render.resolution_x, projection_scene.render.resolution_y = fitted['size']
        projection_scene.render.pixel_aspect_x = projection_scene.render.pixel_aspect_y = 1.
        projection_scene.view_layers[0].update()
        for i in eligible:
            p = body.matrix_world @ mesh.shape_keys.key_blocks['Basis'].data[i].co
            weight = smooth((p.z - 1.570) / .014) * smooth((1.727 - p.z) / .015)
            weight *= smooth((.083 - abs(p.x)) / .016) * smooth((-.022 - p.y) / .040)
            central = smooth((p.z - 1.595) / .014)
            cheek = smooth((abs(p.x) - .044) / .017) * smooth((p.z - 1.575) / .018)
            weight *= max(central, cheek)
            for cx in (.038, -.0355):
                eye = math.hypot((p.x - cx) / .026, (p.z - 1.645) / .015)
                weight *= smooth((eye - 1.) / .40)
            mouth = math.hypot((p.x + .0005) / .041, (p.z - 1.571) / .016)
            weight *= smooth((mouth - 1.10) / .35)
            if weight < .001:
                continue
            counts['eligible'] += 1
            hit, normal, index, _ = tree.ray_cast(Vector((p.x, -.4, p.z)), Vector((0, 1, 0)))
            if hit is None or abs(hit.y - p.y) > .042 or normal.y > -.20:
                counts['rejected'] += 1
                continue
            triangle = triangles[index]
            point = barycentric_transform(hit, *[mapped[j] for j in triangle],
                                          *[raw[j] for j in triangle])
            uv = world_to_camera_view(projection_scene, camera, point)
            if uv.z <= 0 or not (0 < uv.x < 1 and 0 < uv.y < 1):
                counts['rejected'] += 1
                continue
            uv_vertex[i] = uv.xy
            weights[i] = .94 * weight * smooth((-normal.y - .20) / .35)
            counts['projected'] += 1
    finally:
        bpy.data.objects.remove(camera, do_unlink=True)
        bpy.data.cameras.remove(camera_data)
        bpy.data.scenes.remove(projection_scene)
    assert counts['projected'] > 500, 'Insufficient fitted front-photo overlap'
    previous_uv = mesh.uv_layers.active_index
    layer = mesh.uv_layers.new(name='V563_FrontPhotoUV')
    loops = np.empty(len(mesh.loops), np.int32)
    mesh.loops.foreach_get('vertex_index', loops)
    layer.data.foreach_set('uv', uv_vertex[loops].ravel())
    mesh.uv_layers.active_index = previous_uv
    attribute = mesh.attributes.new('V563_FrontPhotoWeight', 'FLOAT', 'POINT')
    attribute.data.foreach_set('value', weights)

    material = original.copy()
    material.name = 'V563_DIRECT_FRONT_PHOTO_SKIN'
    nodes, links = material.node_tree.nodes, material.node_tree.links
    shader = nodes['Principled BSDF']
    previous_color = shader.inputs['Base Color'].links[0].from_socket
    uv_node = nodes.new('ShaderNodeUVMap')
    uv_node.uv_map = layer.name
    image = bpy.data.images.load(str(source / fitted['image']), check_existing=True)
    image.pack()
    texture = nodes.new('ShaderNodeTexImage')
    texture.name = 'V563_UnblendedFrontPortrait'
    texture.image = image
    texture.interpolation = 'Linear'
    texture.extension = 'EXTEND'
    links.new(uv_node.outputs['UV'], texture.inputs['Vector'])
    mask = nodes.new('ShaderNodeAttribute')
    mask.attribute_name = attribute.name
    gain = nodes.new('ShaderNodeMath')
    gain.name = 'V563_FrontPhotoGain'
    gain.operation = 'MULTIPLY'
    gain.inputs[1].default_value = 1.
    links.new(mask.outputs['Fac'], gain.inputs[0])
    mix = nodes.new('ShaderNodeMixRGB')
    mix.name = 'V563_DirectFrontComposite'
    links.new(gain.outputs[0], mix.inputs[0])
    links.new(previous_color, mix.inputs[1])
    links.new(texture.outputs['Color'], mix.inputs[2])
    links.new(mix.outputs[0], shader.inputs['Base Color'])
    mesh.materials.append(material)
    affected_faces = 0
    for polygon in mesh.polygons:
        if polygon.material_index == original_slot:
            polygon.material_index = len(mesh.materials) - 1
            affected_faces += 1
    mesh.update()
    assert len(bpy.data.objects['V357_CLOUDRIG_CONTROLS'].animation_data.drivers) == 1957
    report = {'source_image': fitted['image'], 'source_size': list(image.size),
              'fitted_camera': fitted['source_object'], 'projection': counts,
              'material': material.name, 'affected_faces': affected_faces,
              'maximum_mix': float(weights.max()), 'geometry_changed': False,
              'rig_drivers': 1957, 'uv_layer': layer.name,
              'scope': 'central_forehead_nose_cheeks; eyelids_lips_beard_transition_excluded',
              'status': 'TRIAL_REQUIRES_MATCHED_RENDER_REVIEW'}
    (Path(output) / 'front-photo-report.json').write_text(json.dumps(report, indent=2))
    return report
