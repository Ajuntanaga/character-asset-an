"""Correct imported eye shader scale in a reversible combined-scene trial."""
import json
from pathlib import Path

import bpy


def build(output):
    rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
    assert len(rig.animation_data.drivers) == 1957
    report = {'revision': 'V558', 'materials': {}, 'pupils': {}}
    copies = {}
    for side in ('L', 'R'):
        eye = bpy.data.objects['V374_EYE.' + side]
        assert len(eye.data.materials) == 1
        original = eye.data.materials[0]
        if original.name not in copies:
            material = original.copy()
            material.name = 'V558_BROWN_EYE_WET_SURFACE.' + side
            groups = [n for n in material.node_tree.nodes
                      if n.type == 'GROUP' and n.node_tree
                      and n.node_tree.nodes.get('Ambient Occlusion')
                      and n.node_tree.nodes.get('Principled BSDF')]
            assert len(groups) == 1
            group = groups[0]
            original_group = group.node_tree
            group.node_tree = original_group.copy()
            group.node_tree.name = 'V558_EYE_SURFACE.' + side
            nodes, links = group.node_tree.nodes, group.node_tree.links
            ao = nodes['Ambient Occlusion']
            assert len(ao.inputs['Color'].links) == 1
            albedo = ao.inputs['Color'].links[0].from_socket
            destinations = [link.to_socket for link in ao.outputs['Color'].links]
            assert len(destinations) == 1
            # Cycles already computes scene occlusion. The imported material
            # additionally darkened its base color with a 30 cm AO radius.
            for destination in destinations:
                links.new(albedo, destination)
            bump_changes = {}
            for node in nodes:
                if node.type == 'BUMP':
                    distance = node.inputs['Distance']
                    assert not distance.is_linked
                    bump_changes[node.name] = {'before_m': distance.default_value,
                                               'after_m': .000020}
                    distance.default_value = .000020
            assert bump_changes
            shader = nodes['Principled BSDF']
            previous_specular = shader.inputs['Specular IOR Level'].default_value
            shader.inputs['Specular IOR Level'].default_value = .5
            roughness = shader.inputs['Roughness']
            roughness_source = [(link.from_node.name, link.from_socket.name)
                                for link in roughness.links]
            for link in tuple(roughness.links):
                links.remove(link)
            roughness.default_value = .24
            # Preserve the existing separate corneal cap, iris colors and IOR.
            copies[original.name] = material
            report['materials'][original.name] = {
                'trial': material.name, 'original_group': original_group.name,
                'trial_group': group.node_tree.name,
                'bypassed_ao_distance_m': ao.inputs['Distance'].default_value,
                'bump_distances': bump_changes,
                'previous_specular_ior_level': previous_specular,
                'specular_ior_level': .5, 'roughness': .24,
                'previous_roughness_source': roughness_source,
            }
        eye.data.materials[0] = copies[original.name]
        dilation = eye.data.shape_keys.key_blocks['Dilation']
        report['pupils'][side] = {'previous': dilation.value, 'trial': .90,
                                  'higher_value_contracts_pupil': True}
        dilation.value = .90
    bpy.context.view_layer.update()
    assert len(rig.animation_data.drivers) == 1957
    report['main_drivers'] = 1957
    report['status'] = 'TRIAL_REQUIRES_ACTUAL_RENDER_REVIEW'
    (Path(output) / 'eye-surface-report.json').write_text(json.dumps(report, indent=2))
    return report
