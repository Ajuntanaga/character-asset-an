import bpy,json,math
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'production_v509_loose_pick_pose';out.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER') and 'v508' in bpy.data.filepath
r=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];assert len(r.animation_data.drivers)==1957
names=[f'FK-Finger_{d}{i}.R' for d in ('Middle','Ring','Pinky') for i in (1,2,3)]
p=out/'original_pose.json';assert not p.exists();p.write_text(json.dumps({n:[list(row) for row in r.pose.bones[n].matrix_basis] for n in names}))
for d,angles in [('Middle',(22,38,18)),('Ring',(28,42,20)),('Pinky',(34,46,22))]:
 for i,a in enumerate(angles,1):r.pose.bones[f'FK-Finger_{d}{i}.R'].rotation_euler.x=math.radians(a)
r.update_tag();bpy.context.view_layer.update()
f=root/'pipeline/check_v458_grip_fit.py';exec(compile(f.read_text().replace('production_v458_grip_fit/check.json','production_v509_loose_pick_pose/check.json'),str(f),'exec'),{'__file__':str(f)})
f=root/'pipeline/review_v492_isolated_palm.py'
s=f.read_text().replace('production_v492_palm_review','production_v509_loose_pick_pose/isolated').replace('out.mkdir(exist_ok=True)','out.mkdir(parents=True,exist_ok=True)')
exec(compile(s,str(f),'exec'),{'__file__':str(f)})
p=root/'pipeline/render_preview_request.json';request=json.loads(p.read_text());request.update(output='production_v509_loose_pick_pose/instrument.png',samples=24);p.write_text(json.dumps(request))
f=root/'pipeline/render_preview_job.py';exec(compile(f.read_text(),str(f),'exec'),{'__file__':str(f)})
