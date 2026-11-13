"""Unlit base color: separate atlas/mapping defects from lighting response."""
from pathlib import Path
import runpy
import bpy

head = bpy.data.objects['V740_NATIVE_FACE']
original = list(head.data.materials)
copies = []
try:
    for index, material in enumerate(original):
        diagnostic = material.copy()
        copies.append(diagnostic)
        head.data.materials[index] = diagnostic
        nodes, links = diagnostic.node_tree.nodes, diagnostic.node_tree.links
        shader = next(n for n in nodes if n.type == 'BSDF_PRINCIPLED')
        output = next(n for n in nodes if n.type == 'OUTPUT_MATERIAL' and n.is_active_output)
        emission = nodes.new('ShaderNodeEmission')
        assert shader.inputs['Base Color'].is_linked
        links.new(shader.inputs['Base Color'].links[0].from_socket, emission.inputs['Color'])
        emission.inputs['Strength'].default_value = 1.
        links.new(emission.outputs[0], output.inputs['Surface'])
    runpy.run_path(str(Path(__file__).with_name('render_v740_cloud_groom.py')),
        init_globals={'TEXTURE_PATH': 'Character_An_photoreal_head_basecolor_v326.png',
                      'TAG': 'v740_unlit_basecolor', 'VIEWS': ['front'],
                      'VIEW_TRANSFORM': 'Standard', 'EXPOSURE': 0., 'SAMPLES': 8,
                      'EXCLUDE_OBJECTS': ['V740_NATIVE_CURLS', 'V740_NATIVE_UNDERCOAT',
                                          'V740_BROW_FIBERS', 'V740_BEARD_FIBERS']})
finally:
    for index, material in enumerate(original):
        head.data.materials[index] = material
    for material in copies:
        bpy.data.materials.remove(material)
