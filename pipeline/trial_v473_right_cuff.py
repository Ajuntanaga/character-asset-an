"""Coherent reversible right sleeve tailoring study."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];O=R/'production_v473_right_cuff';O.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
assert 'v471' in bpy.data.filepath
rig=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];assert len(rig.animation_data.drivers)==1957
names=['V416_BODY_CLEAN_JOIN','V421_REGULAR_SLEEVE_CUFF.R','V411_Cuff_Stitches.R','V413_Brass_Cuff_Button.R']
assert not (O/'deltas.json').exists()
report={};backup={}
def smooth(t):
 t=max(0,min(1,t));return t*t*(3-2*t)
a=rig.matrix_world@rig.data.bones['DEF-Forearm_1.R'].head_local
b=rig.matrix_world@rig.data.bones['DEF-Forearm_2.R'].tail_local
axis=b-a
for name in names:
 o=bpy.data.objects[name];changes={}
 jacket={i for p in o.data.polygons if p.material_index==6 for i in p.vertices} if name=='V416_BODY_CLEAN_JOIN' else None
 for v in o.data.vertices:
  p=o.matrix_world@v.co
  if p.x>-.22 or not .88<p.z<1.10:continue
  if jacket is not None and v.index not in jacket:continue
  t=(p-a).dot(axis)/axis.length_squared;c=a+axis*t
  if (p-c).length>.115:continue
  weight=smooth((p.z-.88)/.025)*smooth((1.10-p.z)/.08)
  delta=o.matrix_world.inverted().to_3x3()@((c-p)*(.14*weight))
  changes[v.index]=delta
 if o.data.shape_keys:
  for key in o.data.shape_keys.key_blocks:
   for i,d in changes.items():key.data[i].co+=d
 else:
  for i,d in changes.items():o.data.vertices[i].co+=d
 o.data.update();backup[name]={str(i):list(d) for i,d in changes.items()};report[name]={'changed':len(changes),'max_mm':max((d.length*1000 for d in changes.values()),default=0)}
bpy.context.view_layer.update();(O/'deltas.json').write_text(json.dumps(backup));(O/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
(R/'pipeline/render_preview_request.json').write_text(json.dumps({'output':'production_v473_right_cuff/full.png','resolution':[720,960],'samples':24,'scale':2.12,'camera':[.35,-3.5,1.3],'target':[0,0,.94]}))
f=R/'pipeline/render_preview_job.py';exec(compile(f.read_text(),str(f),'exec'),dict(globals(),__file__=str(f)))
