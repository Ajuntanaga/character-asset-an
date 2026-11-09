"""Use one registered portrait across the lips and their surrounding skin."""
import json
from pathlib import Path

import bpy

from refine_v563_front_photo import smooth


def portrait_weight(point):
    return (.94 * smooth((point.z - 1.523) / .015)
            * smooth((1.625 - point.z) / .020)
            * smooth((.092 - abs(point.x)) / .018)
            * smooth((-.022 - point.y) / .040))


def build(output):
    body = bpy.data.objects['V416_BODY_CLEAN_JOIN']
    lips = bpy.data.objects['V363_LIPS']
    mesh = body.data
    slot = list(mesh.materials).index(bpy.data.materials['V563_DIRECT_FRONT_PHOTO_SKIN'])
    eligible = {i for polygon in mesh.polygons if polygon.material_index == slot
                for i in polygon.vertices}
    attribute = mesh.attributes['V563_FrontPhotoWeight']
    weights = {}
    for i in eligible:
        point = body.matrix_world @ mesh.shape_keys.key_blocks['Basis'].data[i].co
        weight = portrait_weight(point)
        if weight > attribute.data[i].value:
            weights[i] = weight
    # V571 populated excluded vertices too; never blend image corners into skin.
    uv = mesh.uv_layers['V563_FrontPhotoUV'].data
    for polygon in mesh.polygons:
        if polygon.material_index == slot:
            for loop_index in polygon.loop_indices:
                if mesh.loops[loop_index].vertex_index in weights:
                    assert 0 < uv[loop_index].uv.x < 1 and 0 < uv[loop_index].uv.y < 1
    for i, weight in weights.items():
        attribute.data[i].value = weight
    lip_attribute = lips.data.attributes['V574_LipPortraitWeight']
    for i, vertex in enumerate(lips.data.shape_keys.key_blocks['Basis'].data):
        lip_attribute.data[i].value = portrait_weight(lips.matrix_world @ vertex.co)
    body.data.update()
    lips.data.update()
    assert len(bpy.data.objects['V357_CLOUDRIG_CONTROLS'].animation_data.drivers) == 1957
    report = {'extended_body_vertices': len(weights), 'lip_vertices': len(lip_attribute.data),
              'geometry_changed': False, 'rig_drivers': 1957,
              'status': 'TRIAL_REQUIRES_NEUTRAL_AND_EXPRESSION_RENDER_REVIEW'}
    (Path(output) / 'mouth-surround-report.json').write_text(json.dumps(report, indent=2))
    return report
