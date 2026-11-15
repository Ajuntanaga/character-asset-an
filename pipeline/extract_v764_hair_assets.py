"""Bake licensed donor strands into portable arrays, without donor rig scripts."""
import json
import sys
from pathlib import Path

import bpy
import numpy as np

OUT = Path('results/hair-library')
OUT.mkdir(parents=True, exist_ok=True)
mode = sys.argv[sys.argv.index('--') + 1]
report = {'source': mode, 'blender': bpy.app.version_string, 'objects': {}}


def world_points(obj, points):
    matrix = np.asarray(obj.matrix_world, dtype=np.float64)
    return (points @ matrix[:3, :3].T + matrix[:3, 3]).astype(np.float32)


def mesh_array(obj, name):
    mesh = obj.data
    points = np.empty((len(mesh.vertices), 3), dtype=np.float32)
    mesh.vertices.foreach_get('co', points.ravel())
    points = world_points(obj, points)
    mesh.calc_loop_triangles()
    triangles = np.asarray([t.vertices[:] for t in mesh.loop_triangles], dtype=np.int32)
    np.savez_compressed(OUT / (name + '.npz'), points=points, triangles=triangles)
    report['objects'][name] = {'vertices': len(points),
                               'bounds': [points.min(0).tolist(), points.max(0).tolist()]}


def strands(obj, name, evaluate=False):
    source = obj.evaluated_get(bpy.context.evaluated_depsgraph_get()) if evaluate else obj
    data = source.data
    assert isinstance(data, bpy.types.Curves), (name, type(data).__name__)
    lengths = np.asarray([len(c.points) for c in data.curves], dtype=np.int32)
    offsets = np.concatenate(([0], np.cumsum(lengths))).astype(np.int32)
    points = np.empty((len(data.points), 3), dtype=np.float32)
    data.position_data.foreach_get('vector', points.ravel())
    points = world_points(source, points)
    assert offsets[-1] == len(points) and len(lengths) > 0 and lengths.min() >= 2
    assert np.isfinite(points).all()
    roots = points[offsets[:-1]]
    radius = np.full(len(points), .00004, dtype=np.float32)
    attribute = data.attributes.get('radius')
    if attribute and attribute.domain == 'POINT':
        attribute.data.foreach_get('value', radius)
    np.savez_compressed(OUT / (name + '.npz'), points=points, offsets=offsets, radius=radius)
    report['objects'][name] = {
        'original_object': obj.name, 'evaluated': evaluate, 'strands': len(lengths),
        'points': len(points), 'points_per_strand': [int(lengths.min()), int(lengths.max())],
        'root_bounds': [roots.min(0).tolist(), roots.max(0).tolist()],
        'root_quantiles': np.quantile(roots, [0.01, .1, .5, .9, .99], axis=0).tolist(),
        'bounds': [points.min(0).tolist(), points.max(0).tolist()],
        'radius_quantiles': np.quantile(radius, [0, .5, 1]).tolist()}
    print('EXTRACTED', name, len(lengths), len(points), flush=True)


if mode == 'einar':
    # Einar already contains the complete groom; importing its rig/GN is unnecessary.
    for part in ('beard', 'beard.messy', 'eyebrows', 'eyelashes', 'mustache', 'mustache.messy'):
        strands(bpy.data.objects['GEO-einar_' + part], 'einar_' + part)
    mesh_array(bpy.data.objects['GEO-einar_head'], 'einar_head')
elif mode == 'bystedt':
    # Evaluate the artist's entire interpolation/curl/clump graph at render density.
    # A viewport evaluation otherwise exports only a fraction of the finished hair.
    for group in bpy.data.node_groups:
        if group.bl_idname != 'GeometryNodeTree':
            continue
        for node in list(group.nodes):
            if node.bl_idname == 'GeometryNodeIsViewport':
                output_links = list(node.outputs[0].links)
                value = group.nodes.new('FunctionNodeInputBool')
                value.boolean = False
                for link in output_links:
                    target = link.to_socket
                    group.links.remove(link)
                    group.links.new(value.outputs[0], target)
    obj = bpy.data.objects['curly hair']
    for collection in bpy.data.collections:
        collection.hide_viewport = False
    obj.hide_viewport = False
    obj.hide_set(False)
    bpy.context.view_layer.update()
    strands(obj, 'bystedt_curls', evaluate=True)
    assert report['objects']['bystedt_curls']['strands'] > 10000, 'Only guides were evaluated'
    mesh_array(bpy.data.objects['curly growth mesh'], 'bystedt_scalp')
elif mode == 'target':
    head = bpy.data.objects['V740_NATIVE_FACE']
    mesh_array(head, 'target_head')
    report['shape_keys'] = [k.name for k in head.data.shape_keys.key_blocks]
    report['drivers'] = len(bpy.data.objects['V357_CLOUDRIG_CONTROLS'].animation_data.drivers)
    for name in ('V740_NATIVE_CURLS', 'V740_BROW_FIBERS', 'V740_BEARD_FIBERS'):
        obj = bpy.data.objects[name]
        report['objects'][name] = {'type': obj.type, 'bounds': [list(p) for p in obj.bound_box]}
else:
    raise ValueError(mode)
(OUT / (mode + '-extraction.json')).write_text(json.dumps(report, indent=2))
