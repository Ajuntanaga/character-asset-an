"""Compare left skinning modes in open and curl poses; always restore scene."""
import bpy,json,math
from pathlib import Path
root=Path(__file__).resolve().parents[1]
out=root/'production_v495_left_volume';out.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER') and 'v494' in bpy.data.filepath
rig=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];hand=bpy.data.objects['V357_ANATOMICAL_HAND.L']
mod=next(m for m in hand.modifiers if m.type=='ARMATURE')
volume=mod.use_deform_preserve_volume
backup={f'FK-Finger_{f}{i}.L':rig.pose.bones[f'FK-Finger_{f}{i}.L'].matrix_basis.copy() for f in ('Index','Middle','Ring','Pinky') for i in (1,2,3)}
f=root/'pipeline/review_v492_isolated_palm.py'
base=f.read_text().replace('V357_ANATOMICAL_HAND.R','V357_ANATOMICAL_HAND.L').replace('DEF-Hand.R','DEF-Hand.L').replace('out.mkdir(exist_ok=True)','out.mkdir(parents=True,exist_ok=True)')
rows=[]
try:
 for pose in ('open','curl'):
  for n,m in backup.items():rig.pose.bones[n].matrix_basis=m
  for n in backup:rig.pose.bones[n].rotation_euler.x=0 if pose=='open' else math.radians((55,70,45)[int(n[-3])-1])
  rig.update_tag()
  for preserve in (True,False):
   mod.use_deform_preserve_volume=preserve;bpy.context.view_layer.update()
   source=base.replace('production_v492_palm_review','production_v495_left_volume/'+pose+('_volume' if preserve else '_linear'))
   exec(compile(source,str(f),'exec'),{'__file__':str(f)})
   ev=hand.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh()
   rows.append({'pose':pose,'preserve_volume':preserve,'finite':all(math.isfinite(x) for v in mesh.vertices for x in v.co),'vertices':len(mesh.vertices)})
   ev.to_mesh_clear()
finally:
 for n,m in backup.items():rig.pose.bones[n].matrix_basis=m
 mod.use_deform_preserve_volume=volume
 rig.update_tag();bpy.context.view_layer.update()
(out/'pose_checks.json').write_text(json.dumps({'cases':rows,'drivers':len(rig.animation_data.drivers),'restored':True},indent=2))
print(json.dumps(rows))
