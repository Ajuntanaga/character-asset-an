"""Reversible face-domain legacy-head mask; preserves shared clothing vertices."""
import bpy


def build(body):
    """Hide old head faces without deleting mesh, weights, or expression keys."""
    name = 'V757_LegacyHeadMask'
    assert body.type == 'MESH'
    assert body.modifiers.get(name) is None, 'Mask already present'
    assert body.data.attributes.get(name) is None, 'Mask attribute already present'
    materials = [m.name if m else '' for m in body.data.materials]
    protected = {'V379_DARK_COTTON_JACKET', 'V425_Reference_Scale_Botanical_Shirt',
                 'V379_DARK_COTTON_PANTS', 'V426_Scaled_Collar'}
    assert protected <= set(materials), 'Unexpected clothing material layout'
    head_materials = {'V365_LID_SKIN', 'V370_DARK_HAIR_UNDERLAY',
                      'V371_DARK_HAIR_UNDERLAY', 'V372_FACE_SKIN',
                      'V377_REFERENCE_PHOTO_SKIN'}
    keys = body.data.shape_keys
    basis = keys.key_blocks['Basis'].data if keys else body.data.vertices
    world = [body.matrix_world @ v.co for v in basis]
    flags = []
    counts = {}
    for polygon in body.data.polygons:
        material = materials[polygon.material_index]
        center = sum((world[i] for i in polygon.vertices), world[polygon.vertices[0]]*0)/len(polygon.vertices)
        # Region restriction protects hands using the same skin material.
        in_head = abs(center.x) < .15 and center.z > 1.49
        candidate = material in head_materials or material.startswith('tripo_material_')
        hide = in_head and candidate and material not in protected
        flags.append(hide)
        if hide:
            counts[material] = counts.get(material, 0)+1
    assert sum(flags) > 1000, 'Legacy head selection unexpectedly small'
    attribute = body.data.attributes.new(name, 'BOOLEAN', 'FACE')
    attribute.data.foreach_set('value', flags)
    tree = bpy.data.node_groups.new(name, 'GeometryNodeTree')
    tree.interface.new_socket(name='Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    tree.interface.new_socket(name='Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    inp = tree.nodes.new('NodeGroupInput')
    out = tree.nodes.new('NodeGroupOutput')
    attr = tree.nodes.new('GeometryNodeInputNamedAttribute')
    attr.data_type = 'BOOLEAN'
    attr.inputs['Name'].default_value = name
    delete = tree.nodes.new('GeometryNodeDeleteGeometry')
    delete.domain = 'FACE'
    delete.mode = 'ONLY_FACE'
    tree.links.new(inp.outputs['Geometry'], delete.inputs['Geometry'])
    tree.links.new(attr.outputs['Attribute'], delete.inputs['Selection'])
    tree.links.new(delete.outputs['Geometry'], out.inputs['Geometry'])
    modifier = body.modifiers.new(name, 'NODES')
    modifier.node_group = tree
    # Evaluate the face-domain selection before subdivision changes topology.
    with bpy.context.temp_override(object=body, active_object=body):
        bpy.ops.object.modifier_move_to_index(modifier=modifier.name, index=0)
    return {'status': 'MASK_TRIAL_REQUIRES_FULL_BODY_RENDER',
            'masked_faces': sum(flags), 'by_material': counts,
            'protected_materials': sorted(protected),
            'shape_keys_retained': len(keys.key_blocks) if keys else 0}
