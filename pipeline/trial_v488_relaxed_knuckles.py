"""Reversible reference pose trial; preserve pick-driving thumb/index controls."""
import bpy,json,math
from pathlib import Path
from mathutils import Matrix,Vector
root=Path(__file__).resolve().parents[1];out=root/'production_v488_reference_pick_curl';out.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
rig=bpy.data.objects['V357_CLOUDRIG_CONTROLS']
names=[f'FK-Finger_{f}{i}.R' for f in ('Middle','Ring','Pinky') for i in (1,2,3)]
p=out/'original_pose.json'
if not p.exists():p.write_text(json.dumps({n:[list(row) for row in rig.pose.bones[n].matrix_basis] for n in names},indent=2))
for n,m in json.loads(p.read_text()).items():rig.pose.bones[n].matrix_basis=Matrix(m)
rows={}
for finger,angles in [('Middle',(8,62,38)),('Ring',(12,70,42)),('Pinky',(16,75,45))]:
 for i,angle in enumerate(angles,1):
  b=rig.pose.bones[f'FK-Finger_{finger}{i}.R'];rows[b.name]={'before_deg':list(map(math.degrees,b.rotation_euler))};b.rotation_euler.x=math.radians(angle);rows[b.name]['after_deg']=list(map(math.degrees,b.rotation_euler))
rig.update_tag();bpy.context.view_layer.update()
(out/'relaxed_angles.json').write_text(json.dumps(rows,indent=2))
f=root/'pipeline/check_v458_grip_fit.py';exec(compile(f.read_text().replace('production_v458_grip_fit/check.json','production_v488_reference_pick_curl/relaxed_check.json'),str(f),'exec'))
g=bpy.data.objects['V206_GUITAR_ROOT']
(root/'pipeline/render_preview_request.json').write_text(json.dumps({'output':'production_v488_reference_pick_curl/relaxed.png','resolution':[800,700],'samples':24,'scale':.32,'camera':list(g.matrix_world@Vector((.68,.28,.42))),'target':list(g.matrix_world@Vector((.635,-.02,.045)))}))
f=root/'pipeline/render_preview_job.py';exec(compile(f.read_text(),str(f),'exec'),dict(globals(),__file__=str(f)))
