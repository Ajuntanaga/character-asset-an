"""Reversible finger-volume study, preserving grip digits and rig data."""
import bpy,json
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1];out=root/'production_v471_finger_volume';out.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
assert 'v468' in bpy.data.filepath.lower()
backup=out/'original_coordinates.json'
assert backup.exists()
source=json.loads((root/'production_v359_hand_weights/rest_hand_data.json').read_text())['bones']
original={s:[list(v.co) for v in bpy.data.objects['V357_ANATOMICAL_HAND.'+s].data.vertices] for s in ('R','L')}
original=json.loads(backup.read_text())
for side,coords in original.items():
 for v,co in zip(bpy.data.objects['V357_ANATOMICAL_HAND.'+side].data.vertices,coords):v.co=co
report={}
for side in ('R','L'):
 o=bpy.data.objects['V357_ANATOMICAL_HAND.'+side];count=0;maximum=0
 for v in o.data.vertices:
  delta=Vector((0,0,0))
  for w in v.groups:
   n=o.vertex_groups[w.group].name.replace('.R','.L')
   if n not in source or not any('Finger_'+f in n for f in ('Middle','Ring','Pinky')):continue
   a=Vector(source[n]['head']);b=Vector(source[n]['tail']);axis=b-a
   t=max(0,min(1,(v.co-a).dot(axis)/axis.length_squared));c=a+t*axis
   radial=v.co-c
   delta.x+=.18*radial.x*w.weight
   # Keep the palmar contact surface stationary in this first silhouette study.
   if radial.y<0:delta.y+=.10*radial.y*w.weight
  if delta.length>1e-8:v.co+=delta;count+=1;maximum=max(maximum,delta.length)
 o.data.update();o.update_tag();report[side]={'vertices':count,'max_delta_mm':maximum*1000}
bpy.context.view_layer.update();assert len(bpy.data.objects['V357_CLOUDRIG_CONTROLS'].animation_data.drivers)==1957
(out/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
g=bpy.data.objects['V206_GUITAR_ROOT']
(root/'pipeline/render_preview_request.json').write_text(json.dumps({'output':'production_v471_finger_volume/close.png','resolution':[900,700],'samples':24,'scale':.42,'camera':list(g.matrix_world@Vector((.68,.28,.42))),'target':list(g.matrix_world@Vector((.635,-.02,.045)))}))
f=root/'pipeline/render_preview_job.py';exec(compile(f.read_text(),str(f),'exec'),dict(globals(),__file__=str(f)))
