"""Blend the safe unfolding lid texture into the current surrounding face."""
import json
from pathlib import Path

import bpy


def build(output):
    body = bpy.data.objects['V416_BODY_CLEAN_JOIN']
    mesh = body.data
    original = bpy.data.materials['V365_LID_SKIN']
    slot = list(mesh.materials).index(original)
    faces = [p for p in mesh.polygons if p.material_index == slot]
    assert faces
    lid_vertices = {i for p in faces for i in p.vertices}
    surrounding = {i for p in mesh.polygons if p.material_index != slot for i in p.vertices}
    boundary = lid_vertices & surrounding
    blend = mesh.attributes['V365_LidAlbedoBlend']
    assert len(boundary) == 128, len(boundary)
    assert max(abs(blend.data[i].value) for i in boundary) < 1e-6
    assert max(blend.data[i].value for i in lid_vertices) > .999
    assert mesh.uv_layers.get('V365_CleanSkin')
    assert mesh.uv_layers.get('V563_FrontPhotoUV')

    face = bpy.data.materials['V563_DIRECT_FRONT_PHOTO_SKIN']
    material = face.copy()
    material.name = 'V569_CONTINUOUS_FACE_LID_SKIN'
    nodes, links = material.node_tree.nodes, material.node_tree.links
    shader = nodes['Principled BSDF']
    exterior = shader.inputs['Base Color'].links[0].from_socket
    # Preserve the adjacent-skin UV sampling used by the existing blink. The
    # inner lid must not acquire a photographed eye when it unfolds.
    uv = nodes.new('ShaderNodeUVMap')
    uv.uv_map = 'V365_CleanSkin'
    clean_source = next(n for n in original.node_tree.nodes if n.type == 'TEX_IMAGE'
                        and n.inputs['Vector'].is_linked
                        and n.inputs['Vector'].links[0].from_node.type == 'UVMAP'
                        and n.inputs['Vector'].links[0].from_node.uv_map == uv.uv_map)
    texture = nodes.new('ShaderNodeTexImage')
    texture.name = 'V569_SafeUnfoldingLidTexture'
    texture.image = clean_source.image
    texture.interpolation = clean_source.interpolation
    texture.extension = clean_source.extension
    links.new(uv.outputs['UV'], texture.inputs['Vector'])
    correction_source = original.node_tree.nodes['V372_Complexion']
    correction = nodes.new('ShaderNodeMixRGB')
    correction.name = 'V569_LidComplexion'
    correction.blend_type = correction_source.blend_type
    correction.inputs[2].default_value = correction_source.inputs[2].default_value
    complexion_weight = nodes.new('ShaderNodeAttribute')
    complexion_weight.attribute_name = 'V372_HeadSkin'
    links.new(complexion_weight.outputs['Fac'], correction.inputs[0])
    links.new(texture.outputs['Color'], correction.inputs[1])
    attribute = nodes.new('ShaderNodeAttribute')
    attribute.attribute_name = blend.name
    composite = nodes.new('ShaderNodeMixRGB')
    composite.name = 'V569_LidToFaceTransition'
    links.new(attribute.outputs['Fac'], composite.inputs[0])
    links.new(exterior, composite.inputs[1])
    links.new(correction.outputs[0], composite.inputs[2])
    links.new(composite.outputs[0], shader.inputs['Base Color'])
    mesh.materials.append(material)
    for polygon in faces:
        polygon.material_index = len(mesh.materials) - 1
    mesh.update()
    assert len(bpy.data.objects['V357_CLOUDRIG_CONTROLS'].animation_data.drivers) == 1957
    report = {'material': material.name, 'previous_material': original.name,
              'exterior_material': face.name, 'affected_faces': len(faces),
              'welded_boundary_vertices': len(boundary),
              'maximum_boundary_inner_mix': max(blend.data[i].value for i in boundary),
              'geometry_changed': False, 'blink_changed': False, 'main_drivers': 1957,
              'status': 'TRIAL_REQUIRES_BLINK_AND_CLAY_RENDER_REVIEW'}
    (Path(output) / 'lid-skin-transition-report.json').write_text(json.dumps(report, indent=2))
    return report
