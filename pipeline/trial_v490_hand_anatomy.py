"""Reversible palm taper and phalange cross-section shaping, no weight edits."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1];out=root/'production_v490_hand_anatomy';out.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
p=out/'original_coordinates.json';assert not p.exists()
source=json.loads((root/'production_v359_hand_weights/rest_hand_data.json').read_text())['bones']
original={s:[list(v.co) for v in bpy.data.objects['V357_ANATOMICAL_HAND.'+s].data.vertices] for s in ('R','L')};p.write_text(json.dumps(original));report={}
for side in ('R','L'):
 o=bpy.data.objects['V357_ANATOMICAL_HAND.'+side];nails={i for p in o.data.polygons if p.material_index==1 for i in p.vertices};deltas=[]
 for v in o.data.vertices:
  if v.index in nails:continue
  co=v.co.copy();weights={o.vertex_groups[w.group].name.replace('.R','.L'):w.weight for w in v.groups}
  if any(w>.001 and ('Thumb' in n or 'Index' in n) for n,w in weights.items()):continue
  delta=Vector()
  # Taper ulnar midpalm, blending to untouched wrist and finger roots.
  t=(-co.z-.025)/.080
  if 0<t<1 and co.x<.01:
   delta.x+=.004*math.sin(math.pi*t)**2*min(1,max(0,(.01-co.x)/.05))
  # Flatten central dorsal PIP/DIP crowns, retaining lateral joint shoulders.
  # Reduce excess palmar pad depth gently instead of shrinking the whole digit.
  for name,w in weights.items():
   if name not in source or not any('Finger_'+f in name for f in ('Middle','Ring','Pinky')):continue
   a=Vector(source[name]['head']);b=Vector(source[name]['tail']);axis=b-a
   t=max(0,min(1,(co-a).dot(axis)/axis.length_squared));radial=co-(a+t*axis)
   if radial.y<0:
    center=math.exp(-(radial.x/.006)**4)
    joints=math.exp(-((t*axis.length)/.008)**2)+math.exp(-(((1-t)*axis.length)/.008)**2)
    if name.endswith('1.L'):joints=math.exp(-(((1-t)*axis.length)/.008)**2)
    delta.y+=min(.0022,-radial.y*.28)*center*min(1,joints)*w
   else:delta.y-=.14*radial.y*w
  if delta.length>1e-7:v.co+=delta;deltas.append(delta.length)
 o.data.update();o.update_tag();report[side]={'changed':len(deltas),'max_mm':max(deltas)*1000}
bpy.context.view_layer.update();report['drivers']=len(bpy.data.objects['V357_CLOUDRIG_CONTROLS'].animation_data.drivers);assert report['drivers']==1957
(out/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
f=root/'pipeline/trial_v488_relaxed_knuckles.py';s=f.read_text().replace('production_v488_reference_pick_curl/relaxed_check.json','production_v490_hand_anatomy/check.json').replace('production_v488_reference_pick_curl/relaxed.png','production_v490_hand_anatomy/curl.png');exec(compile(s,str(f),'exec'),dict(globals(),__file__=str(f)))
