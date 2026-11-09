"""Compare coordinated three-finger curls, preserving all rig drivers."""
import bpy,json,math
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'production_v516_reference_curl';out.mkdir(exist_ok=True)
assert 'v514' in bpy.data.filepath and not bpy.app.is_job_running('RENDER')
rig=bpy.data.objects['V357_CLOUDRIG_CONTROLS']
names=[f'FK-Finger_{f}{i}.R' for f in ('Middle','Ring','Pinky') for i in (1,2,3)]
original={n:rig.pose.bones[n].matrix_basis.copy() for n in names}
backup=out/'original.json';assert not backup.exists()
backup.write_text(json.dumps({n:[list(row) for row in m] for n,m in original.items()}))
def update():
 rig.update_tag();bpy.context.view_layer.update()
def review(label):
 update()
 f=root/'pipeline/review_v492_isolated_palm.py'
 code=f.read_text().replace('production_v492_palm_review','production_v516_reference_curl/'+label).replace('out.mkdir(exist_ok=True)','out.mkdir(parents=True,exist_ok=True)')
 exec(compile(code,str(f),'exec'),{'__file__':str(f)})
 f=root/'pipeline/check_v458_grip_fit.py'
 exec(compile(f.read_text().replace('production_v458_grip_fit','production_v516_reference_curl/'+label),str(f),'exec'),{'__file__':str(f)})
try:
 for label,angles in [('distributed',[(25,65,45),(30,70,45),(35,75,45)]),('relaxed',[(20,45,30),(25,50,35),(30,55,40)])]:
  for finger,values in zip(('Middle','Ring','Pinky'),angles):
   for joint,value in enumerate(values,1):rig.pose.bones[f'FK-Finger_{finger}{joint}.R'].rotation_euler.x=math.radians(value)
  review(label)
finally:
 for n,m in original.items():rig.pose.bones[n].matrix_basis=m
 update();assert len(rig.animation_data.drivers)==1957
 (out/'restored.json').write_text(json.dumps({'restored':True,'drivers':1957,'filepath':bpy.data.filepath}))
print('V516 comparisons complete; original pose restored')
