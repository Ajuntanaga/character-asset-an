"""Intermediate joint detail between smooth V460 and engraved V440; reversible material copy."""
import bpy,json
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'production_v481_hand_joint_detail';out.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
assert 'v478' in bpy.data.filepath
assert not (out/'materials.json').exists()
backup={}
for side in ('R','L'):
 h=bpy.data.objects['V357_ANATOMICAL_HAND.'+side];backup[side]=h.data.materials[0].name
 m=h.data.materials[0].copy();m.name='V481_Joint_Detail.'+side;h.data.materials[0]=m
 n=m.node_tree.nodes;l=m.node_tree.links;b=n['Shallow joint folds']
 b.inputs['Distance'].default_value=.00028;b.inputs['Strength'].default_value=.48
 mix=n['Mix (Legacy)'];factor=mix.inputs[0].links[0].from_node;factor.inputs[1].default_value=.06
 l.new(mix.outputs[0],n['Principled BSDF'].inputs['Base Color'])
(out/'materials.json').write_text(json.dumps(backup,indent=2))
(out/'mode.txt').write_text('open')
p=root/'pipeline/check_v472_hand_deformation.py';s=p.read_text().replace('production_v472_hand_deformation','production_v481_hand_joint_detail')
exec(compile(s,str(p),'exec'),dict(globals(),__file__=str(p)))
