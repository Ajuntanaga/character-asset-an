import bpy,json,math
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'production_v500_finger_proportions';out.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER') and 'v497' in bpy.data.filepath
r=bpy.data.objects['V357_CLOUDRIG_CONTROLS']
names=[f'FK-Finger_{d}{i}.{s}' for s in ('L','R') for d in ('Index','Middle','Ring','Pinky') for i in (1,2,3)]
backup={n:[list(row) for row in r.pose.bones[n].matrix_basis] for n in names}
p=out/'original_pose.json';assert not p.exists();p.write_text(json.dumps(backup))
for n in names:
 if n.split('.')[0].endswith('1'):r.pose.bones[n].scale.y=1.25
r.update_tag();bpy.context.view_layer.update()
report={n:r.pose.bones[n.replace('FK-','DEF-')].length for n in names};(out/'lengths.json').write_text(json.dumps(report,indent=2))
f=root/'pipeline/review_v492_isolated_palm.py'
s=f.read_text().replace('production_v492_palm_review','production_v500_finger_proportions/playing').replace('out.mkdir(exist_ok=True)','out.mkdir(parents=True,exist_ok=True)')
exec(compile(s,str(f),'exec'),{'__file__':str(f)})
playing={n:r.pose.bones[n].rotation_euler.copy() for n in names}
try:
 for n in names:r.pose.bones[n].rotation_euler.x=0
 r.update_tag();bpy.context.view_layer.update()
 exec(compile(s.replace('/playing','/open'),str(f),'exec'),{'__file__':str(f)})
finally:
 for n,e in playing.items():r.pose.bones[n].rotation_euler=e
 r.update_tag();bpy.context.view_layer.update()
assert len(r.animation_data.drivers)==1957
print('V500 proportion trial ready, original pose backed up')
