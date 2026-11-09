"""Review candidate proportions without clearing animation or original backup."""
import bpy,json,math
from pathlib import Path
from mathutils import Matrix,Vector
root=Path(__file__).resolve().parents[1];out=root/'production_v484_finger_length';r=bpy.data.objects['V357_CLOUDRIG_CONTROLS']
assert not bpy.app.is_job_running('RENDER') and 'v484' in bpy.data.filepath
mode=(out/'review_mode.txt').read_text().strip()
p=out/'review_playing_pose.json'
names=[f'FK-Finger_{f}{i}.{s}' for s in ('R','L') for f in ('Thumb','Index','Middle','Ring','Pinky') for i in (1,2,3)]
if not p.exists():p.write_text(json.dumps({n:[list(row) for row in r.pose.bones[n].matrix_basis] for n in names}))
for n,m in json.loads(p.read_text()).items():r.pose.bones[n].matrix_basis=Matrix(m)
if mode!='restore':
 for s in ('R','L'):
  for f in ('Index','Middle','Ring','Pinky'):
   for i,a in enumerate((0,0,0) if mode=='open' else (55,70,45),1):r.pose.bones[f'FK-Finger_{f}{i}.{s}'].rotation_euler.x=math.radians(a)
r.update_tag();bpy.context.view_layer.update()
report={'mode':mode,'drivers':len(r.animation_data.drivers),'hands':{}}
for s in ('L','R'):
 o=bpy.data.objects['V357_ANATOMICAL_HAND.'+s].evaluated_get(bpy.context.evaluated_depsgraph_get())
 report['hands'][s]={'vertices':len(o.data.vertices),'finite':all(math.isfinite(c) for v in o.data.vertices for c in v.co)}
(out/f'{mode}_check.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
if mode!='restore':
 g=bpy.data.objects['V206_GUITAR_ROOT'];cam=g.matrix_world@Vector((.68,.28,.42));target=g.matrix_world@Vector((.635,-.02,.045))
 (root/'pipeline/render_preview_request.json').write_text(json.dumps({'output':f'production_v484_finger_length/{mode}.png','resolution':[800,700],'samples':24,'scale':.32,'camera':list(cam),'target':list(target)}))
 f=root/'pipeline/render_preview_job.py';exec(compile(f.read_text(),str(f),'exec'),dict(globals(),__file__=str(f)))
