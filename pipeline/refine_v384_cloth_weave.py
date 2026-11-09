"""Use the free measured fabric weave at physical scale on the existing clothes."""
from pathlib import Path
import json
import bpy

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'production_v384_cloth_weave'
OUT.mkdir(exist_ok=True)
ASSET = ROOT/'assets/polyhaven/denim_fabric_03'
scene = bpy.context.scene
assert not bpy.app.is_job_running('RENDER')
rig = bpy.data.objects['V357_CLOUDRIG_CONTROLS']
body = bpy.data.objects['V357_TRIPO_CHARACTER_BODY_BOUND']
assert len(rig.animation_data.drivers) == 1957
assert not body.get('V384_cloth_weave_applied')

maps = {}
for channel, suffix in [('height', 'disp'), ('roughness', 'rough')]:
    image = bpy.data.images.load(str(ASSET/f'denim_fabric_03_{suffix}_2k.jpg'),
                                 check_existing=True)
    image.colorspace_settings.name = 'Non-Color'
    image.pack()
    maps[channel] = image

report = {'source':json.loads((ASSET/'SOURCE.json').read_text()), 'materials':{}}
for name,tint in [('V379_DARK_COTTON_JACKET',(.19,.205,.20,1.)),
                  ('V379_DARK_COTTON_PANTS',(.20,.215,.21,1.))]:
    mat = bpy.data.materials[name]
    nodes,links = mat.node_tree.nodes,mat.node_tree.links
    shader = nodes['Principled BSDF']
    color = nodes['V379_ReferenceFabricColor']
    report['materials'][name] = {'previous_tint':list(color.inputs[2].default_value),
                                 'new_tint':list(tint)}
    color.inputs[2].default_value = tint
    shader.inputs['Specular IOR Level'].default_value = .18
    shader.inputs['Sheen Weight'].default_value = .13
    shader.inputs['Sheen Roughness'].default_value = .75
    shader.inputs['Diffuse Roughness'].default_value = .30
    position = nodes.new('ShaderNodeAttribute')
    position.name = 'V384_StableClothCoordinates'
    position.attribute_name = 'V372_RestPosition'
    scale = nodes.new('ShaderNodeVectorMath')
    scale.operation = 'SCALE'
    scale.inputs['Scale'].default_value = 1./.271
    links.new(position.outputs['Vector'],scale.inputs[0])
    textures = {}
    for channel,image in maps.items():
        tex = nodes.new('ShaderNodeTexImage')
        tex.name = 'V384_Weave_'+channel
        tex.image = image
        tex.projection = 'BOX'
        tex.projection_blend = .25
        tex.extension = 'REPEAT'
        links.new(scale.outputs['Vector'],tex.inputs['Vector'])
        textures[channel] = tex
    roughness = nodes.new('ShaderNodeMath')
    roughness.operation = 'MULTIPLY_ADD'
    roughness.inputs[1].default_value = .20
    roughness.inputs[2].default_value = .70
    links.new(textures['roughness'].outputs['Color'],roughness.inputs[0])
    links.new(roughness.outputs[0],shader.inputs['Roughness'])
    bump = nodes.new('ShaderNodeBump')
    bump.name = 'V384_PhysicalWeave'
    bump.inputs['Strength'].default_value = .35
    bump.inputs['Distance'].default_value = .00014
    if shader.inputs['Normal'].is_linked:
        links.new(shader.inputs['Normal'].links[0].from_socket,bump.inputs['Normal'])
    links.new(textures['height'].outputs['Color'],bump.inputs['Height'])
    links.new(bump.outputs['Normal'],shader.inputs['Normal'])

body['V384_cloth_weave_applied'] = True
report['rig_drivers'] = len(rig.animation_data.drivers)
(OUT/'cloth_weave_report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
