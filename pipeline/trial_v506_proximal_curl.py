"""Redistribute picking curl toward MCP instead of hooked distal joints."""
import bpy,json,math
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'production_v506_proximal_curl';out.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
rig=bpy.data.objects['V357_CLOUDRIG_CONTROLS']
names=[f'FK-Finger_{f}{i}.R' for f in ('Middle','Ring','Pinky') for i in (1,2,3)]
p=out/'original_pose.json';assert not p.exists()
p.write_text(json.dumps({n:[list(row) for row in rig.pose.bones[n].matrix_basis] for n in names}))
for f,a in [('Middle',40),('Ring',45),('Pinky',50)]:
 for i,v in enumerate((a,60,25),1):rig.pose.bones[f'FK-Finger_{f}{i}.R'].rotation_euler.x=math.radians(v)
rig.update_tag();bpy.context.view_layer.update()
f=root/'pipeline/review_v492_isolated_palm.py'
s=f.read_text().replace('production_v492_palm_review','production_v506_proximal_curl/playing').replace('out.mkdir(exist_ok=True)','out.mkdir(parents=True,exist_ok=True)')
exec(compile(s,str(f),'exec'),{'__file__':str(f)})
f=root/'pipeline/check_v458_grip_fit.py';s=f.read_text().replace('production_v458_grip_fit/check.json','production_v506_proximal_curl/check.json')
exec(compile(s,str(f),'exec'),{'__file__':str(f)})
