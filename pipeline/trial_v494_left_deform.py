"""Compare left hand subdivision order, restoring pose and stack afterward."""
import bpy,json,math
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'production_v494_left_deform';out.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
assert 'v493' in bpy.data.filepath
rig=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];hand=bpy.data.objects['V357_ANATOMICAL_HAND.L']
assert [m.type for m in hand.modifiers]==['MULTIRES','ARMATURE']
backup={f'FK-Finger_{finger}{i}.L':rig.pose.bones[f'FK-Finger_{finger}{i}.L'].matrix_basis.copy() for finger in ('Index','Middle','Ring','Pinky') for i in (1,2,3)}
(out/'playing_pose.json').write_text(json.dumps({n:[list(r) for r in m] for n,m in backup.items()}))
f=root/'pipeline/review_v492_isolated_palm.py'
base=f.read_text().replace('V357_ANATOMICAL_HAND.R','V357_ANATOMICAL_HAND.L').replace('DEF-Hand.R','DEF-Hand.L').replace('out.mkdir(exist_ok=True)','out.mkdir(parents=True,exist_ok=True)')
rows=[]
try:
 for pose in ('playing','open'):
  for n,m in backup.items():rig.pose.bones[n].matrix_basis=m
  if pose=='open':
   for n in backup:rig.pose.bones[n].rotation_euler.x=0
  rig.update_tag()
  for order in ('original','trial'):
   if hand.modifiers[0].type=='ARMATURE':hand.modifiers.move(0,1)
   if order=='trial':hand.modifiers.move(1,0)
   bpy.context.view_layer.update()
   source=base.replace('production_v492_palm_review','production_v494_left_deform/'+pose+'_'+order)
   exec(compile(source,str(f),'exec'),{'__file__':str(f)})
   ev=hand.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh()
   rows.append({'pose':pose,'order':order,'finite':all(math.isfinite(x) for v in mesh.vertices for x in v.co),'vertices':len(mesh.vertices)})
   ev.to_mesh_clear()
finally:
 for n,m in backup.items():rig.pose.bones[n].matrix_basis=m
 if hand.modifiers[0].type=='ARMATURE':hand.modifiers.move(0,1)
 rig.update_tag();bpy.context.view_layer.update()
(out/'checks.json').write_text(json.dumps({'cases':rows,'drivers':len(rig.animation_data.drivers),'restored':True},indent=2))
print(json.dumps(rows))
