"""Add existing CC0 denim weave to the replacement cuffs in rest coordinates."""
import bpy,json
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'production_v441_cuff_weave';out.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
rig=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];assert len(rig.animation_data.drivers)==1957
mat=bpy.data.materials['V402_Charcoal_Cotton_Cuff'].copy();mat.name='V441_Rest_Weave_Cuffs'
n,l=mat.node_tree.nodes,mat.node_tree.links
p=next(x for x in n if x.type=='BSDF_PRINCIPLED')
a=n.new('ShaderNodeAttribute');a.attribute_name='V441_CuffRest'
s=n.new('ShaderNodeVectorMath');s.operation='SCALE';s.inputs['Scale'].default_value=1/.271;l.new(a.outputs['Vector'],s.inputs[0])
for channel,suffix in [('height','disp'),('roughness','rough')]:
 im=bpy.data.images.load(str(root/'assets/polyhaven/denim_fabric_03'/f'denim_fabric_03_{suffix}_2k.jpg'),check_existing=True);im.colorspace_settings.name='Non-Color';im.pack()
 t=n.new('ShaderNodeTexImage');t.name='V441_Weave_'+channel;t.image=im;t.projection='BOX';t.projection_blend=.25;l.new(s.outputs['Vector'],t.inputs['Vector'])
 if channel=='height':
  b=n.new('ShaderNodeBump');b.inputs['Strength'].default_value=.45;b.inputs['Distance'].default_value=.00018
  if p.inputs['Normal'].is_linked:l.new(p.inputs['Normal'].links[0].from_socket,b.inputs['Normal'])
  l.new(t.outputs['Color'],b.inputs['Height']);l.new(b.outputs['Normal'],p.inputs['Normal'])
 else:
  m=n.new('ShaderNodeMath');m.operation='MULTIPLY_ADD';m.inputs[1].default_value=.2;m.inputs[2].default_value=.7;l.new(t.outputs['Color'],m.inputs[0]);l.new(m.outputs[0],p.inputs['Roughness'])
p.inputs['Sheen Weight'].default_value=.13;p.inputs['Sheen Roughness'].default_value=.75
for name in ['V421_REGULAR_SLEEVE_CUFF.R','V357_CUFF_PATCH.L']:
 o=bpy.data.objects[name];o.data=o.data.copy();attr=o.data.attributes.new('V441_CuffRest','FLOAT_VECTOR','POINT')
 for v,d in zip(o.data.vertices,attr.data):d.vector=v.co
 for slot in o.material_slots:
  if slot.material and slot.material.name=='V402_Charcoal_Cotton_Cuff':slot.material=mat
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Character_An_cuff_weave_v441.blend'))
print(json.dumps({'saved':bpy.data.filepath,'drivers':len(rig.animation_data.drivers)}))
