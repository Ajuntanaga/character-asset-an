"""Subtle charcoal check from the design lock, fixed in garment rest space."""
import bpy


def build(material):
    nodes, links = material.node_tree.nodes, material.node_tree.links
    coordinates = nodes.new('ShaderNodeAttribute')
    coordinates.name = 'V561_CheckRestPosition'
    coordinates.attribute_name = 'V372_RestPosition'
    separate = nodes.new('ShaderNodeSeparateXYZ')
    links.new(coordinates.outputs['Vector'], separate.inputs[0])
    bands = []
    for axis, period in (('X', .026), ('Z', .030)):
        frequency = nodes.new('ShaderNodeMath')
        frequency.name = 'V561_CheckFrequency_' + axis
        frequency.operation = 'MULTIPLY'
        frequency.inputs[1].default_value = 2. / period
        links.new(separate.outputs[axis], frequency.inputs[0])
        triangle = nodes.new('ShaderNodeMath')
        triangle.operation = 'PINGPONG'
        triangle.inputs[1].default_value = 1.
        links.new(frequency.outputs[0], triangle.inputs[0])
        line = nodes.new('ShaderNodeMapRange')
        line.name = 'V561_CheckLine_' + axis
        line.interpolation_type = 'SMOOTHERSTEP'
        line.clamp = True
        # Symmetric 1 mm core, feathering to zero at 1.6 mm total width.
        line.inputs['From Min'].default_value = .0010 / period
        line.inputs['From Max'].default_value = .0016 / period
        line.inputs['To Min'].default_value = 1.
        line.inputs['To Max'].default_value = 0.
        links.new(triangle.outputs[0], line.inputs['Value'])
        bands.append(line.outputs[0])
    combined = nodes.new('ShaderNodeMath')
    combined.name = 'V561_CheckCrosshatch'
    combined.operation = 'MAXIMUM'
    for index, band in enumerate(bands):
        links.new(band, combined.inputs[index])
    tint = nodes.new('ShaderNodeMixRGB')
    tint.name = 'V561_SubtleCoolCheck'
    tint.blend_type = 'MULTIPLY'
    tint.inputs[2].default_value = (1.08, 1.10, 1.12, 1.)
    links.new(combined.outputs[0], tint.inputs[0])
    links.new(nodes['V388_CharcoalAlbedo'].outputs[0], tint.inputs[1])
    links.new(tint.outputs[0], nodes['V388_UnlitFabricBlend'].inputs[1])
    return {'source': 'references/source/approved_character_design_lock.png',
            'coordinates': 'V372_RestPosition_X_Z',
            'period_m': [.026, .030], 'line_core_m': .001,
            'line_feathered_width_m': .0016, 'line_albedo_multiplier': [1.08, 1.10, 1.12],
            'colored_details_and_shirt': 'UNCHANGED',
            'status': 'SUBTLE_REFERENCE_TRIAL_REQUIRES_TORSO_REVIEW'}
