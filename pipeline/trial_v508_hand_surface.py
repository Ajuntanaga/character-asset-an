"""Reversible rest-anchored hand surface trial; no geometry or pose edits."""
import bpy,json
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'production_v508_hand_surface';out.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER') and 'v507' in bpy.data.filepath
rig=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];assert len(rig.animation_data.drivers)==1957
backup=out/'materials.json';assert not backup.exists()
backup.write_text(json.dumps({s:bpy.data.objects['V357_ANATOMICAL_HAND.'+s].data.materials[0].name for s in ('L','R')}))
for side in ('L','R'):
 h=bpy.data.objects['V357_ANATOMICAL_HAND.'+side];m=h.data.materials[0].copy();m.name='V508_Mature_Hand_Surface.'+side;h.data.materials[0]=m
 n=m.node_tree.nodes;l=m.node_tree.links;p=n['Principled BSDF'];fold=n['Shallow joint folds']
 rest=n.new('ShaderNodeAttribute');rest.attribute_name='V423_rest_position';rest.label='Stable undeformed surface'
 # Mildly meander the existing folds rather than engraving regular straight bands.
 warp=n.new('ShaderNodeTexNoise');warp.inputs['Scale'].default_value=650;warp.inputs['Detail'].default_value=2;l.new(rest.outputs['Vector'],warp.inputs['Vector'])
 subtract=n.new('ShaderNodeVectorMath');subtract.operation='SUBTRACT';subtract.inputs[1].default_value=(.5,.5,.5);l.new(warp.outputs['Color'],subtract.inputs[0])
 scale=n.new('ShaderNodeVectorMath');scale.operation='SCALE';scale.inputs['Scale'].default_value=.00065;l.new(subtract.outputs['Vector'],scale.inputs[0])
 add=n.new('ShaderNodeVectorMath');add.operation='ADD';l.new(rest.outputs['Vector'],add.inputs[0]);l.new(scale.outputs['Vector'],add.inputs[1])
 for group in [x for x in n if x.type=='GROUP' and 'Rest' in x.inputs]:l.new(add.outputs['Vector'],group.inputs['Rest'])
 # Low-amplitude fine skin furrows, below the primary joint folds.
 cells=n.new('ShaderNodeTexVoronoi');cells.feature='DISTANCE_TO_EDGE';cells.inputs['Scale'].default_value=1250;l.new(rest.outputs['Vector'],cells.inputs['Vector'])
 ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.012;ramp.color_ramp.elements[0].color=(0,0,0,1);ramp.color_ramp.elements[1].position=.11;ramp.color_ramp.elements[1].color=(1,1,1,1);l.new(cells.outputs['Distance'],ramp.inputs[0])
 bump=n.new('ShaderNodeBump');bump.name='V508 Fine skin furrows';bump.inputs['Distance'].default_value=.000055;bump.inputs['Strength'].default_value=.32;l.new(ramp.outputs['Color'],bump.inputs['Height']);l.new(fold.outputs['Normal'],bump.inputs['Normal']);l.new(bump.outputs['Normal'],p.inputs['Normal'])
 # Sparse, low-contrast pigment rather than a uniform clay colour.
 pigment=n.new('ShaderNodeTexNoise');pigment.inputs['Scale'].default_value=310; pigment.inputs['Detail'].default_value=3;l.new(rest.outputs['Vector'],pigment.inputs['Vector'])
 pigment_ramp=n.new('ShaderNodeValToRGB');pigment_ramp.color_ramp.elements[0].position=.48;pigment_ramp.color_ramp.elements[0].color=(1,1,1,1);pigment_ramp.color_ramp.elements[1].position=.76;pigment_ramp.color_ramp.elements[1].color=(.63,.47,.35,1);l.new(pigment.outputs['Fac'],pigment_ramp.inputs[0])
 color=p.inputs['Base Color'].links[0].from_socket
 mix=n.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=.32;l.new(color,mix.inputs[1]);l.new(pigment_ramp.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],p.inputs['Base Color'])
 fold.inputs['Distance'].default_value=.00034;fold.inputs['Strength'].default_value=.58
bpy.context.view_layer.update()
request=json.loads((root/'pipeline/render_preview_request.json').read_text());request.update(output='production_v508_hand_surface/instrument.png',resolution=[800,700],samples=64,scale=.32,camera=[-.006247750949,-.645000040531,.743708372116],target=[-.102349579334,-.270000010729,1.031439900398]);(root/'pipeline/render_preview_request.json').write_text(json.dumps(request))
f=root/'pipeline/render_preview_job.py';exec(compile(f.read_text(),str(f),'exec'),{'__file__':str(f)})
