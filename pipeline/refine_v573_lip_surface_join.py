"""Blend the overlapping lip boundary normals with the surrounding face."""
import json
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree


def build(output):
    body = bpy.data.objects['V416_BODY_CLEAN_JOIN']
    lips = bpy.data.objects['V363_LIPS']
    rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
    assert len(rig.animation_data.drivers) == 1957
    assert not lips.get('V573_applied')
    body_keys, lip_keys = body.data.shape_keys.key_blocks, lips.data.shape_keys.key_blocks
    basis = body_keys['Basis']
    body.data.calc_loop_triangles()
    region = {i for i, v in enumerate(basis.data)
              if abs(v.co.x) < .10 and 1.515 < v.co.z < 1.620 and v.co.y < -.030}
    triangles = [tuple(t.vertices) for t in body.data.loop_triangles
                 if all(i in region for i in t.vertices)]
    indices = sorted({i for tri in triangles for i in tri})
    remap = {i: j for j, i in enumerate(indices)}
    triangles = [tuple(remap[i] for i in tri) for tri in triangles]
    report = {'geometry_changed': False, 'aperture_changed': False, 'rig_drivers': 1957}
    points = [body.matrix_world @ basis.data[i].co for i in indices]
    tree = BVHTree.FromPolygons(points, triangles, all_triangles=True)
    group = lips.vertex_groups.new(name='V573_OuterJoin')
    weighted = 0
    for i, vertex in enumerate(lip_keys['Basis'].data):
        _, _, _, distance = tree.find_nearest(lips.matrix_world @ vertex.co)
        value = max(0., min(1., (.006 - distance) / .004))
        value = value * value * (3. - 2. * value)
        if value:
            group.add([i], value, 'REPLACE')
            weighted += 1
    normals = lips.modifiers.new('V573_FaceJoinNormals', 'DATA_TRANSFER')
    normals.object = body
    normals.use_loop_data = True
    normals.data_types_loops = {'CUSTOM_NORMAL'}
    normals.loop_mapping = 'POLYINTERP_NEAREST'
    normals.use_max_distance = True
    normals.max_distance = .008
    normals.vertex_group = group.name
    report['normal_blend_vertices'] = weighted
    lips['V573_applied'] = True
    report['status'] = 'TRIAL_REQUIRES_NEUTRAL_AND_EXPRESSION_RENDER_REVIEW'
    (Path(output) / 'lip-join-report.json').write_text(json.dumps(report, indent=2))
    return report
