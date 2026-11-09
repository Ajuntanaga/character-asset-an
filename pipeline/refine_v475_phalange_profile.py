"""Restore longitudinal phalange taper instead of uniformly inflated tubes."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1];out=root/'production_v475_phalange_profile';out.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
assert 'v473' in bpy.data.filepath
backup=out/'original_coordinates.json';assert not backup.exists()
source=json.loads((root/'production_v359_hand_weights/rest_hand_data.json').read_text())['bones']
original={s:[list(v.co) for v in bpy.data.objects['V357_ANATOMICAL_HAND.'+s].data.vertices] for s in ('R','L')}
backup.write_text(json.dumps(original));report={}
for side in ('R','L'):
 o=bpy.data.objects['V357_ANATOMICAL_HAND.'+side];count=0;maximum=0
 nails={i for p in o.data.polygons if p.material_index==1 for i in p.vertices}
 for v in o.data.vertices:
  if v.index in nails:continue
  weights={o.vertex_groups[w.group].name.replace('.R','.L'):w.weight for w in v.groups}
  if any(w>.001 and ('Index' in n or 'Thumb' in n) for n,w in weights.items()):continue
  delta=Vector()
  for name,weight in weights.items():
   if name not in source or not any('Finger_'+f in name for f in ('Middle','Ring','Pinky')):continue
   a=Vector(source[name]['head']);b=Vector(source[name]['tail']);axis=b-a
   t=(v.co-a).dot(axis)/axis.length_squared
   if not 0<t<1:continue
   radial=v.co-(a+t*axis)
   # Narrow the shaft between joint heads; retain joint envelopes and pad depth.
   f=math.sin(math.pi*t)**2
   strength=.20 if name.endswith('1.L') else .14 if name.endswith('2.L') else .04
   delta.x-=strength*f*radial.x*weight
   if radial.y<0:delta.y-=.08*f*radial.y*weight
  if delta.length>1e-7:v.co+=delta;count+=1;maximum=max(maximum,delta.length)
 o.data.update();o.update_tag();report[side]={'vertices':count,'max_delta_mm':maximum*1000}
bpy.context.view_layer.update();assert len(bpy.data.objects['V357_CLOUDRIG_CONTROLS'].animation_data.drivers)==1957
(out/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
p=root/'pipeline/check_v472_hand_deformation.py'
s=p.read_text().replace('production_v472_hand_deformation','production_v475_phalange_profile')
(out/'mode.txt').write_text('open')
exec(compile(s,str(p),'exec'),dict(globals(),__file__=str(p)))
