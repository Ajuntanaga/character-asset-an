"""Remove prior artificial transverse joint inflation, preserving shaft volume."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1];out=root/'production_v482_joint_width';out.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
assert 'v481' in bpy.data.filepath
assert not (out/'original_coordinates.json').exists()
source=json.loads((root/'production_v359_hand_weights/rest_hand_data.json').read_text())['bones']
old=json.loads((root/'production_v471_finger_volume/original_coordinates.json').read_text())
original={s:[list(v.co) for v in bpy.data.objects['V357_ANATOMICAL_HAND.'+s].data.vertices] for s in ('R','L')}
(out/'original_coordinates.json').write_text(json.dumps(original));report={}
for side in ('R','L'):
 o=bpy.data.objects['V357_ANATOMICAL_HAND.'+side];count=0;maximum=0
 nails={i for p in o.data.polygons if p.material_index==1 for i in p.vertices}
 for v in o.data.vertices:
  if v.index in nails:continue
  co=Vector(old[side][v.index]);dx=0
  for w in v.groups:
   n=o.vertex_groups[w.group].name.replace('.R','.L')
   if n not in source or not any('Finger_'+f in n for f in ('Middle','Ring','Pinky')):continue
   a=Vector(source[n]['head']);b=Vector(source[n]['tail']);axis=b-a
   t=max(0,min(1,(co-a).dot(axis)/axis.length_squared));radial=co-(a+t*axis)
   # Full reversal at joint ends, zero at shaft midpoint; no depth change.
   dx-=.18*radial.x*w.weight*math.cos(math.pi*t)**4
  v.co.x+=dx
  if abs(dx)>1e-7:count+=1;maximum=max(maximum,abs(dx))
 o.data.update();o.update_tag();report[side]={'vertices':count,'maximum_mm':maximum*1000}
bpy.context.view_layer.update();assert len(bpy.data.objects['V357_CLOUDRIG_CONTROLS'].animation_data.drivers)==1957
(out/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
(out/'mode.txt').write_text('open')
p=root/'pipeline/check_v472_hand_deformation.py';s=p.read_text().replace('production_v472_hand_deformation','production_v482_joint_width')
exec(compile(s,str(p),'exec'),dict(globals(),__file__=str(p)))
