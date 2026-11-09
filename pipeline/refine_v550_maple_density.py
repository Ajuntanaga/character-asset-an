"""Increase figured-maple frequency without changing the traced guitar geometry."""
import json
from pathlib import Path
import bpy


def build(output):
    out = Path(output).resolve()
    out.mkdir(parents=True, exist_ok=True)
    top = bpy.data.objects['V206_FIGURED_TOP']
    original = bpy.data.materials['V356_GRAYBURST_FLAMED_MAPLE']
    assert any(slot.material == original for slot in top.material_slots)
    assert not bpy.data.materials.get('V550_DENSE_FIGURED_MAPLE')
    material = original.copy()
    material.name = 'V550_DENSE_FIGURED_MAPLE'
    nodes, links = material.node_tree.nodes, material.node_tree.links
    texture = nodes['V387_FiguredMaple']
    source = texture.inputs['Vector'].links[0].from_socket
    mapping = nodes.new('ShaderNodeMapping')
    mapping.name = 'V550_FigureDensity'
    mapping.vector_type = 'POINT'
    mapping.inputs['Location'].default_value = (0, -.75, 0)
    mapping.inputs['Scale'].default_value = (1, 2.5, 1)
    links.new(source, mapping.inputs['Vector'])
    links.new(mapping.outputs['Vector'], texture.inputs['Vector'])
    texture.extension = 'MIRROR'
    contrast = nodes.new('ShaderNodeRGBCurve')
    contrast.name = 'V550_FigureContrast'
    contrast.mapping.curves[3].points.new(.35, .18)
    contrast.mapping.curves[3].points.new(.62, .82)
    contrast.mapping.update()
    links.new(texture.outputs['Color'], contrast.inputs['Color'])
    links.new(contrast.outputs['Color'], nodes['V387_GrayStain'].inputs[1])
    for slot in top.material_slots:
        if slot.material == original:
            slot.material = material
    material['V550_density_applied'] = True
    rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
    assert len(rig.animation_data.drivers) == 1957
    path = out / 'Character_An_maple_density_TRIAL_v550.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(path), compress=True)
    report = {'status': 'TRIAL_REQUIRES_VISUAL_REVIEW', 'original_material': original.name,
              'trial_material': material.name, 'longitudinal_density': 2.5,
              'figure_contrast_points': [[.35, .18], [.62, .82]],
              'geometry_changed': False, 'burst_changed': False, 'main_drivers': 1957,
              'output': path.name}
    (out / 'maple-density-report.json').write_text(json.dumps(report, indent=2))
    return report
