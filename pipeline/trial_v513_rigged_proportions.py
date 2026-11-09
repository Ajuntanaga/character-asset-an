"""Compare actual rigged open proportions and a bounded length adjustment."""
import bpy,json,math
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'production_v513_rigged_proportions';out.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER') and 'v508' in bpy.data.filepath
r=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];names=[f'FK-Finger_{f}{i}.R' for f in ('Index','Middle','Ring','Pinky') for i in (1,2,3)]
original={n:r.pose.bones[n].matrix_basis.copy() for n in names}
p=out/'original_pose.json';assert not p.exists();p.write_text(json.dumps({n:[list(row) for row in m] for n,m in original.items()}))
f=root/'pipeline/review_v492_isolated_palm.py'
def render(label):
 r.update_tag();bpy.context.view_layer.update()
 s=f.read_text().replace('production_v492_palm_review','production_v513_rigged_proportions/'+label).replace('out.mkdir(exist_ok=True)','out.mkdir(parents=True,exist_ok=True)')
 exec(compile(s,str(f),'exec'),{'__file__':str(f)})
try:
 for n in names:r.pose.bones[n].rotation_euler.x=0
 render('baseline_open')
 for finger in ('Index','Middle','Ring','Pinky'):r.pose.bones[f'FK-Finger_{finger}1.R'].scale.y=1.4
 render('trial_open')
 for n,m in original.items():r.pose.bones[n].matrix_basis=m
 for finger in ('Index','Middle','Ring','Pinky'):r.pose.bones[f'FK-Finger_{finger}1.R'].scale.y=1.4
 render('trial_playing')
 (out/'candidate_pose.json').write_text(json.dumps({n:[list(row) for row in r.pose.bones[n].matrix_basis] for n in names}))
finally:
 for n,m in original.items():r.pose.bones[n].matrix_basis=m
 r.update_tag();bpy.context.view_layer.update()
 assert len(r.animation_data.drivers)==1957
 (out/'restored.json').write_text(json.dumps({'restored':True,'drivers':1957}))
print('V513 comparison rendered; original pose restored')
