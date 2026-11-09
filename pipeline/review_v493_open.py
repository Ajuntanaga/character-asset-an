import bpy,json
from pathlib import Path
from mathutils import Matrix
root=Path(__file__).resolve().parents[1];out=root/'production_v493_deform_order'
rig=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];hand=bpy.data.objects['V357_ANATOMICAL_HAND.R']
assert not bpy.app.is_job_running('RENDER')
backup={f'FK-Finger_{finger}{i}.R':rig.pose.bones[f'FK-Finger_{finger}{i}.R'].matrix_basis.copy() for finger in ('Index','Middle','Ring','Pinky') for i in (1,2,3)}
(out/'playing_pose.json').write_text(json.dumps({n:[list(r) for r in m] for n,m in backup.items()}))
try:
 for n in backup:rig.pose.bones[n].rotation_euler.x=0
 rig.update_tag();bpy.context.view_layer.update()
 f=root/'pipeline/review_v492_isolated_palm.py'
 for label in ('open_original','open_trial'):
  if label=='open_trial':hand.modifiers.move(1,0)
  bpy.context.view_layer.update()
  source=f.read_text().replace('production_v492_palm_review','production_v493_deform_order/'+label).replace('out.mkdir(exist_ok=True)','out.mkdir(parents=True,exist_ok=True)')
  exec(compile(source,str(f),'exec'),{'__file__':str(f)})
finally:
 for n,m in backup.items():rig.pose.bones[n].matrix_basis=m
 if hand.modifiers[0].type=='ARMATURE':hand.modifiers.move(0,1)
 rig.update_tag();bpy.context.view_layer.update()
print('Original pose and modifier order restored')
