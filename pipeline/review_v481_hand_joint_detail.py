import bpy,json,random
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1];out=root/'production_v481_hand_joint_detail'
assert not bpy.app.is_job_running('RENDER')
# Stable joint-specific variation, shared on left and right; no driver or mesh changes.
if not (out/'varied.json').exists():
 for side in ('R','L'):
  m=bpy.data.objects['V357_ANATOMICAL_HAND.'+side].data.materials[0];assert m.name.startswith('V481')
  for n in m.node_tree.nodes:
   if n.type!='GROUP':continue
   rng=random.Random(n.label);n.inputs['Width'].default_value*=rng.uniform(.78,1.04)
   center=Vector(n.inputs['Center'].default_value);axis=Vector(n.inputs['Axis'].default_value)
   n.inputs['Center'].default_value=center+axis*rng.uniform(-.0005,.0005)
 (out/'varied.json').write_text(json.dumps({'width_factor':[.78,1.04],'offset_m':[-.0005,.0005]}))
(out/'mode.txt').write_text('curl')
p=root/'pipeline/check_v472_hand_deformation.py';s=p.read_text().replace('production_v472_hand_deformation','production_v481_hand_joint_detail')
exec(compile(s,str(p),'exec'),dict(globals(),__file__=str(p)))
