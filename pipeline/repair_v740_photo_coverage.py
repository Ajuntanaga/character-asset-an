"""Trial bilateral skin sampling; preserve native UVs for surface-bound hair."""
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform


def repair_photo_coverage(head, skin, coordinates):
    mesh = head.data
    native = mesh.uv_layers['UVMap']
    original = np.array([loop.uv[:] for loop in native.data])
    active_index = mesh.uv_layers.active_index
    mesh.calc_loop_triangles()
    # V736 donor alignment translates its symmetry plane to x=1.6mm.
    center = .0016
    triangles = [t for t in mesh.loop_triangles
                 if coordinates[list(t.vertices), 0].mean() > center]
    tree = BVHTree.FromPolygons([Vector(p) for p in coordinates],
                               [tuple(t.vertices) for t in triangles],
                               all_triangles=True)
    repaired = mesh.uv_layers.new(name='V740_ObservedSidePhotoUV')
    sampled = {}
    distances = []
    for vertex, point in enumerate(coordinates):
        if point[0] >= center-.015:
            continue
        reflected = Vector((2*center-point[0], point[1], point[2]))
        hit, normal, index, distance = tree.find_nearest(reflected)
        assert hit is not None, vertex
        triangle = triangles[index]
        xyz = [Vector(coordinates[i]) for i in triangle.vertices]
        tex = [Vector((*original[i], 0)) for i in triangle.loops]
        sampled[vertex] = barycentric_transform(hit, *xyz, *tex).xy
        distances.append(distance)
    for loop in mesh.loops:
        repaired.data[loop.index].uv = sampled.get(loop.vertex_index, original[loop.index])
    mesh.uv_layers.active_index = active_index
    native.active_render = True
    assert np.array_equal(original, np.array([loop.uv[:] for loop in native.data]))
    weight = np.clip((center-.015-coordinates[:, 0])/.025, 0, 1)
    weight = weight*weight*(3-2*weight)
    attribute = mesh.attributes.new('V740_ObservedSidePhotoBlend', 'FLOAT', 'POINT')
    attribute.data.foreach_set('value', weight.astype(np.float32))
    nodes, links = skin.node_tree.nodes, skin.node_tree.links
    source = next(n for n in nodes if n.type == 'TEX_IMAGE' and n.image
                  and Path(n.image.filepath).name == 'Character_An_photoreal_head_basecolor_v326.png')
    consumers = [link.to_socket for link in source.outputs['Color'].links]
    assert consumers
    mirrored = nodes.new('ShaderNodeTexImage')
    mirrored.image = source.image
    mirrored.interpolation = source.interpolation
    mirrored.extension = source.extension
    uv = nodes.new('ShaderNodeUVMap')
    uv.uv_map = repaired.name
    links.new(uv.outputs['UV'], mirrored.inputs['Vector'])
    mask = nodes.new('ShaderNodeAttribute')
    mask.attribute_name = attribute.name
    mix = nodes.new('ShaderNodeMixRGB')
    mix.label = 'Observed side coverage repair trial'
    links.new(mask.outputs['Fac'], mix.inputs[0])
    links.new(source.outputs['Color'], mix.inputs[1])
    links.new(mirrored.outputs['Color'], mix.inputs[2])
    for socket in consumers:
        links.new(mix.outputs['Color'], socket)
    assert sampled and np.isfinite(distances).all()
    return {'method': 'reflected surface barycentric UV color blend',
            'native_uv_preserved': True, 'sampled_vertices': len(sampled),
            'symmetry_plane_x_mm': center*1000,
            'projection_distance_mm_p50_p95_max': (np.percentile(distances, [50, 95, 100])*1000).tolist(),
            'status': 'unreviewed texture symmetry trial; source asymmetry lost in repaired region'}
