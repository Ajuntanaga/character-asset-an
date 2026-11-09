"""Bounded curl search preserving thumb/index and restoring baseline per candidate."""
import bpy,json,math,io,contextlib
from pathlib import Path
from mathutils import Matrix,Vector
root=Path(__file__).resolve().parents[1];out=root/'production_v491_pick_curl';out.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
assert 'v490' in bpy.data.filepath
rig=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];names=[f'FK-Finger_{f}{i}.R' for f in ('Middle','Ring','Pinky') for i in (1,2,3)]
p=out/'original_pose.json';assert not p.exists()
backup={n:[list(row) for row in rig.pose.bones[n].matrix_basis] for n in names};p.write_text(json.dumps(backup))
check=root/'pipeline/check_v458_grip_fit.py';source=check.read_text().replace('production_v458_grip_fit/check.json','production_v491_pick_curl/check.json')
rows=[]
def apply(a,b,c):
 for n,m in backup.items():rig.pose.bones[n].matrix_basis=Matrix(m)
 for f,offset in [('Middle',0),('Ring',4),('Pinky',8)]:
  for i,v in enumerate((a+offset,b,c),1):rig.pose.bones[f'FK-Finger_{f}{i}.R'].rotation_euler.x=math.radians(v)
 rig.update_tag();bpy.context.view_layer.update()
for a in (-20,-10,0,10):
 for b in (45,65,85):
  for c in (30,50):
   apply(a,b,c)
   with contextlib.redirect_stdout(io.StringIO()):exec(compile(source,str(check),'exec'),{})
   r=json.loads((out/'check.json').read_text());r['angles']=[a,b,c];rows.append(r)
(out/'sweep.json').write_text(json.dumps(rows,indent=2))
safe=[r for r in rows if not r['crossed_string_centrelines'] and r['sampled_clearance_m']>.0003]
if safe:
 best=min(safe,key=lambda r:sum((v-t)**2 for v,t in zip(r['angles'],(8,65,40))))
 apply(*best['angles']);(out/'selected.json').write_text(json.dumps(best,indent=2));print(json.dumps(best))
 g=bpy.data.objects['V206_GUITAR_ROOT']
 (root/'pipeline/render_preview_request.json').write_text(json.dumps({'output':'production_v491_pick_curl/trial.png','resolution':[800,700],'samples':24,'scale':.32,'camera':list(g.matrix_world@Vector((.68,.28,.42))),'target':list(g.matrix_world@Vector((.635,-.02,.045)))}))
 f=root/'pipeline/render_preview_job.py';exec(compile(f.read_text(),str(f),'exec'),dict(globals(),__file__=str(f)))
else:
 for n,m in backup.items():rig.pose.bones[n].matrix_basis=Matrix(m)
 rig.update_tag();bpy.context.view_layer.update();print(json.dumps({'safe_candidates':0,'restored':True,'best_margin':max(r['sampled_clearance_m'] for r in rows)}))
