"""Soften over-deep joint shader folds without changing hand geometry or pose."""
import bpy,json
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1];out=root/'production_v460_hand_skin';out.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
assert 'v459' in bpy.data.filepath
report={}
for side in ('L','R'):
 hand=bpy.data.objects['V357_ANATOMICAL_HAND.'+side]
 slot=next(s for s in hand.material_slots if s.material and s.material.name.startswith('V440_Readable_Joint_Folds'))
 m=slot.material.copy();m.name='V460_Soft_Hand_Folds.'+side;slot.material=m
 n=m.node_tree.nodes;b=n.get('Shallow joint folds')
 b.inputs['Distance'].default_value=.00016;b.inputs['Strength'].default_value=.32
 # Remove extra dark stripe overlay added in V440; preserve underlying skin color.
 p=n.get('Principled BSDF');mix=p.inputs['Base Color'].links[0].from_node
 assert mix.bl_idname=='ShaderNodeMixRGB' and mix.blend_type=='MULTIPLY'
 color=mix.inputs[1].links[0].from_socket;m.node_tree.links.new(color,p.inputs['Base Color'])
 report[side]={'fold_distance_m':.00016,'fold_strength':.32,'dark_stripe_overlay':False}
report['rig_drivers']=len(bpy.data.objects['V357_CLOUDRIG_CONTROLS'].animation_data.drivers)
(out/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
g=bpy.data.objects['V206_GUITAR_ROOT'];cam=g.matrix_world@Vector((.68,.28,.42));look=g.matrix_world@Vector((.635,-.02,.045))
(root/'pipeline/render_preview_request.json').write_text(json.dumps({'output':'production_v460_hand_skin/v460_hand.png','resolution':[720,640],'samples':24,'scale':.23,'camera':list(cam),'target':list(look)}))
f=root/'pipeline/render_preview_job.py';exec(compile(f.read_text(),str(f),'exec'),dict(globals(),__file__=str(f)))
