"""Reversible open/curl hand review; never clears animation or drivers."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector,Matrix
root=Path(__file__).resolve().parents[1];out=root/'production_v472_hand_deformation';out.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
r=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];g=bpy.data.objects['V206_GUITAR_ROOT']
mode=(out/'mode.txt').read_text().strip()
names=[f'FK-Finger_{f}{i}.R' for f in ('Thumb','Index','Middle','Ring','Pinky') for i in (1,2,3)]
backup=out/'original_pose.json'
if not backup.exists():backup.write_text(json.dumps({n:[list(row) for row in r.pose.bones[n].matrix_basis] for n in names}))
original=json.loads(backup.read_text())
for n,m in original.items():r.pose.bones[n].matrix_basis=Matrix(m)
if mode!='restore':
 for f in ('Index','Middle','Ring','Pinky'):
  for i,a in enumerate((0,0,0) if mode=='open' else (55,70,45),1):
   b=r.pose.bones[f'FK-Finger_{f}{i}.R'];b.rotation_euler.x=math.radians(a)
r.update_tag();bpy.context.view_layer.update()
assert len(r.animation_data.drivers)==1957
if mode=='restore':
 print('Original playing pose restored; 1957 rig drivers retained')
else:
 e=bpy.data.objects['V357_ANATOMICAL_HAND.R'].evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh()
 try:
  report={'pose':mode,'vertices':len(m.vertices),'finite':all(math.isfinite(c) for v in m.vertices for c in v.co),'rig_drivers':len(r.animation_data.drivers),'scope':'Static pose inspection; not animation or collision acceptance'}
 finally:e.to_mesh_clear()
 (out/f'{mode}_check.json').write_text(json.dumps(report,indent=2))
 cam=g.matrix_world@Vector((.68,.28,.42));target=g.matrix_world@Vector((.635,-.02,.045))
 (root/'pipeline/render_preview_request.json').write_text(json.dumps({'output':f'production_v472_hand_deformation/{mode}.png','resolution':[800,700],'samples':24,'scale':.30,'camera':list(cam),'target':list(target)}))
 p=root/'pipeline/render_preview_job.py';exec(compile(p.read_text(),str(p),'exec'),dict(globals(),__file__=str(p)))
