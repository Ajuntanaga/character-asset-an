"""Reduce baked neutral highlights while retaining colored garment details."""
from pathlib import Path
import bpy,json
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'production_v388_cloth_albedo'
OUT.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
rig=bpy.data.objects['V357_CLOUDRIG_CONTROLS']
assert len(rig.animation_data.drivers)==1957
report={}
for name in ('V379_DARK_COTTON_JACKET','V379_DARK_COTTON_PANTS'):
    mat=bpy.data.materials[name]
    assert not mat.get('V388_albedo_applied')
    nodes,links=mat.node_tree.nodes,mat.node_tree.links
    source=nodes['Image Texture'].outputs['Color']
    gray=nodes.new('ShaderNodeRGBToBW')
    links.new(source,gray.inputs[0])
    ramp=nodes.new('ShaderNodeValToRGB')
    ramp.name='V388_CharcoalAlbedo'
    ramp.color_ramp.elements[0].position=0.
    ramp.color_ramp.elements[0].color=(.004,.005,.005,1)
    ramp.color_ramp.elements[1].position=.65
    ramp.color_ramp.elements[1].color=(.026,.029,.028,1)
    links.new(gray.outputs[0],ramp.inputs[0])
    hsv=nodes.new('ShaderNodeSeparateColor')
    hsv.mode='HSV'
    links.new(source,hsv.inputs[0])
    mask=nodes.new('ShaderNodeMapRange')
    mask.name='V388_PreserveColoredDetails'
    mask.clamp=True
    mask.inputs['From Min'].default_value=.18
    mask.inputs['From Max'].default_value=.38
    links.new(hsv.outputs[1],mask.inputs['Value'])
    mix=nodes.new('ShaderNodeMixRGB')
    mix.name='V388_UnlitFabricBlend'
    links.new(mask.outputs[0],mix.inputs[0])
    links.new(ramp.outputs[0],mix.inputs[1])
    links.new(nodes['V379_ReferenceFabricColor'].outputs[0],mix.inputs[2])
    shader=nodes['Principled BSDF']
    links.new(mix.outputs[0],shader.inputs['Base Color'])
    shader.inputs['Sheen Weight'].default_value=.06
    mat['V388_albedo_applied']=True
    report[name]={'neutral_albedo_range':[.004,.029],'colored_detail_saturation_range':[.18,.38]}
report['rig_drivers']=1957
(OUT/'cloth_report.json').write_text(json.dumps(report,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Character_An_charcoal_cloth_v388.blend'),compress=True)
print(json.dumps(report))
