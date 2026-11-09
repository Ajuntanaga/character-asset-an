"""Reference maple finish and reversible hardware; retain the traced body."""
import json
from pathlib import Path
import bpy


def build(output, save=True):
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
    image_path = Path(__file__).resolve().parents[1] / 'assets/generated/gray_maple_v553/gray_curly_maple_albedo.png'
    texture.image = bpy.data.images.load(str(image_path), check_existing=True)
    texture.image.pack()
    source = texture.inputs['Vector'].links[0].from_socket
    mapping = nodes.new('ShaderNodeMapping')
    mapping.name = 'V550_FigureDensity'
    mapping.vector_type = 'POINT'
    mapping.inputs['Location'].default_value = (0, 0, 0)
    mapping.inputs['Scale'].default_value = (1, 1, 1)
    links.new(source, mapping.inputs['Vector'])
    links.new(mapping.outputs['Vector'], texture.inputs['Vector'])
    texture.extension = 'MIRROR'
    luminance = nodes.new('ShaderNodeRGBToBW')
    luminance.name = 'V552_MapleLuminance'
    links.new(texture.outputs['Color'], luminance.inputs['Color'])
    contrast = nodes.new('ShaderNodeRGBCurve')
    contrast.name = 'V550_FigureContrast'
    # New broad-flame albedo: decoded luminance p05/p95 are .287/.491.
    # Keep the flame visible without amplifying fine longitudinal grain into
    # white scratches. The reference has a restrained silver/olive center.
    contrast.mapping.curves[3].points.new(.287, .18)
    contrast.mapping.curves[3].points.new(.491, .48)
    contrast.mapping.update()
    links.new(luminance.outputs['Val'], contrast.inputs['Color'])
    links.new(contrast.outputs['Color'], nodes['V387_GrayStain'].inputs[1])
    nodes['V387_GrayStain'].inputs[2].default_value = (.47, .52, .45, 1)
    nodes['V380_BurstFalloff'].inputs[1].default_value = 3.5
    edge_object = bpy.data.objects['V206_BODY_CORE']
    edge_original = bpy.data.materials['V356_NATURAL_MAPLE_EDGE']
    edge_material = edge_original.copy()
    edge_material.name = 'V550_CHARCOAL_BODY_EDGE'
    edge_shader = edge_material.node_tree.nodes['Principled BSDF']
    edge_shader.inputs['Base Color'].default_value = (.009, .012, .010, 1)
    edge_shader.inputs['Roughness'].default_value = .42
    for slot in edge_object.material_slots:
        if slot.material == edge_original:
            slot.material = edge_material
    for slot in top.material_slots:
        if slot.material == original:
            slot.material = material
    material['V550_density_applied'] = True
    from refine_v552_guitar_hardware import build as build_hardware
    hardware = build_hardware()
    rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
    assert len(rig.animation_data.drivers) == 1957
    path = out / 'Character_An_maple_density_TRIAL_v550.blend'
    if save:
        bpy.ops.wm.save_as_mainfile(filepath=str(path), compress=True)
    report = {'status': 'TRIAL_REQUIRES_VISUAL_REVIEW', 'original_material': original.name,
              'trial_material': material.name, 'longitudinal_density': 1.0,
              'texture': 'assets/generated/gray_maple_v553/gray_curly_maple_albedo.png',
              'figure_contrast_points': [[.287, .18], [.491, .48]],
              'stain_tint': [.47, .52, .45, 1],
              'edge_material': edge_material.name,
              'body_geometry_changed': False, 'hardware': hardware,
              'burst_changed': True, 'burst_exponent': 3.5, 'main_drivers': 1957,
              'output': path.name if save else None}
    (out / 'maple-density-report.json').write_text(json.dumps(report, indent=2))
    return report
