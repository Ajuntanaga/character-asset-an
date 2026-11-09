"""Match cuff response to the charcoal jacket while keeping existing weave maps."""
import bpy,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'production_v445_cuff_fabric';O.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
assert bpy.data.filepath.endswith('Character_An_sleeve_volume_v444.blend')
rig=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];assert len(rig.animation_data.drivers)==1957
old=bpy.data.materials['V441_Rest_Weave_Cuffs'];m=old.copy();m.name='V445_Charcoal_Cuff_Fabric'
n=m.node_tree.nodes;l=m.node_tree.links;bs=n.get('Principled BSDF')
bs.inputs['Specular IOR Level'].default_value=.18
bs.inputs['Sheen Weight'].default_value=.06
bs.inputs['Diffuse Roughness'].default_value=.3
ramp=n.new('ShaderNodeValToRGB');ramp.name='V445_Charcoal_Weave_Albedo'
ramp.color_ramp.elements[0].color=(.009,.011,.0105,1)
ramp.color_ramp.elements[1].color=(.018,.021,.020,1)
l.new(n['V441_Weave_height'].outputs['Color'],ramp.inputs[0]);l.new(ramp.outputs['Color'],bs.inputs['Base Color'])
for name in ['V357_CUFF_PATCH.L','V421_REGULAR_SLEEVE_CUFF.R']:
 o=bpy.data.objects[name]
 for i,mat in enumerate(o.data.materials):
  if mat==old:o.data.materials[i]=m
bpy.ops.wm.save_as_mainfile(filepath=str(O/'Character_An_cuff_fabric_v445.blend'),compress=True)
print(json.dumps({'material':m.name,'drivers':len(rig.animation_data.drivers)}))
