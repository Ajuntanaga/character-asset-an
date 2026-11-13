"""Restore the native donor hand's photographic skin and nail texture maps."""
import json
from pathlib import Path

import bpy


def build(output, texture_dir=None, hand_name='V528_NATIVE_HAND.R'):
    root = Path(__file__).resolve().parents[1]
    textures = Path(texture_dir) if texture_dir else root / 'github_assets/antonia-hand'
    hand = bpy.data.objects[hand_name]
    if hand_name == 'V528_NATIVE_HAND.R':
        assert len(hand.data.vertices) == 3311
    assert hand.type == 'MESH'
    assert all(p.material_index in (0, 1) for p in hand.data.polygons)
    assert len(hand.data.materials) == 2
    assert hand.data.uv_layers.get('UVMap') is not None
    assert len(bpy.data.objects['V357_CLOUDRIG_CONTROLS'].animation_data.drivers) == 1957
    previous = [material.name for material in hand.data.materials]
    images = {}
    for channel in ('albedo', 'bump', 'gloss'):
        path = textures / ('arms_' + channel + '.png')
        image = bpy.data.images.load(str(path), check_existing=True)
        image.colorspace_settings.name = 'sRGB' if channel == 'albedo' else 'Non-Color'
        image.pack()
        images[channel] = image
    materials = []
    for nail in (False, True):
        material = bpy.data.materials.new('V585_Antonia_' + ('Nails' if nail else 'Hand_Skin'))
        material.use_nodes = True
        nodes, links = material.node_tree.nodes, material.node_tree.links
        shader = nodes.get('Principled BSDF')
        shader.inputs['IOR'].default_value = 1.45
        shader.inputs['Specular IOR Level'].default_value = .35
        shader.inputs['Subsurface Weight'].default_value = .03 if nail else .10
        shader.inputs['Subsurface Scale'].default_value = .001
        shader.inputs['Subsurface Radius'].default_value = (1., .35, .20)
        uv = nodes.new('ShaderNodeUVMap')
        uv.uv_map = 'UVMap'
        maps = {}
        for channel, image in images.items():
            tex = nodes.new('ShaderNodeTexImage')
            tex.name = 'V585_' + channel
            tex.image = image
            links.new(uv.outputs['UV'], tex.inputs['Vector'])
            maps[channel] = tex
        links.new(maps['albedo'].outputs['Color'], shader.inputs['Base Color'])
        roughness = nodes.new('ShaderNodeMapRange')
        roughness.inputs['From Min'].default_value = 0.
        roughness.inputs['From Max'].default_value = 1.
        roughness.inputs['To Min'].default_value = .40 if nail else .62
        roughness.inputs['To Max'].default_value = .26 if nail else .36
        links.new(maps['gloss'].outputs['Color'], roughness.inputs['Value'])
        links.new(roughness.outputs['Result'], shader.inputs['Roughness'])
        bump = nodes.new('ShaderNodeBump')
        bump.inputs['Distance'].default_value = .00022
        bump.inputs['Strength'].default_value = .20 if nail else .35
        links.new(maps['bump'].outputs['Color'], bump.inputs['Height'])
        links.new(bump.outputs['Normal'], shader.inputs['Normal'])
        materials.append(material)
    for index, material in enumerate(materials):
        hand.data.materials[index] = material
    report = {'object': hand.name, 'previous_materials': previous,
              'materials': [material.name for material in materials],
              'textures': {channel: image.name for channel, image in images.items()},
              'uv_map': 'UVMap', 'geometry_and_pose_changed': False,
              'main_drivers': 1957,
              'status': 'MATERIAL_TRIAL_REQUIRES_VISUAL_REVIEW'}
    out = Path(output)
    out.mkdir(parents=True, exist_ok=True)
    (out / 'native-hand-surface-report.json').write_text(json.dumps(report, indent=2))
    return report
