"""Make existing rest-anchored joint folds readable in close lighting."""
import bpy,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'production_v440_hand_folds';O.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
assert 'v439' in bpy.data.filepath
for side in ['L','R']:
 h=bpy.data.objects['V357_ANATOMICAL_HAND.'+side]
 slot=next(s for s in h.material_slots if s.material and s.material.name.startswith('V424_Rest_Skin'))
 m=slot.material.copy();m.name='V440_Readable_Joint_Folds.'+side;slot.material=m
 n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF');b=n.get('Shallow joint folds')
 b.inputs['Distance'].default_value=.00055;b.inputs['Strength'].default_value=.75
 mask=b.inputs['Height'].links[0].from_socket
 scale=n.new('ShaderNodeMath');scale.operation='MULTIPLY';scale.inputs[1].default_value=.22;l.new(mask,scale.inputs[0])
 color=p.inputs['Base Color'].links[0].from_socket
 mix=n.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[2].default_value=(.55,.40,.30,1)
 l.new(scale.outputs[0],mix.inputs[0]);l.new(color,mix.inputs[1]);l.new(mix.outputs[0],p.inputs['Base Color'])
assert len(bpy.data.objects['V357_CLOUDRIG_CONTROLS'].animation_data.drivers)==1957
bpy.ops.wm.save_as_mainfile(filepath=str(O/'Character_An_hand_folds_v440.blend'))
print('Saved material candidate; pose and geometry unchanged')
