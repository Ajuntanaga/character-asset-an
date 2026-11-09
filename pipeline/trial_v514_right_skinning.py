"""Compare right-hand linear skinning in playing and open poses, then restore."""
import bpy,json,math
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'production_v514_right_skinning';out.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER') and 'v508' in bpy.data.filepath
rig=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];hand=bpy.data.objects['V357_ANATOMICAL_HAND.R']
mod=next(m for m in hand.modifiers if m.type=='ARMATURE');volume=mod.use_deform_preserve_volume
names=[f'FK-Finger_{f}{i}.R' for f in ('Index','Middle','Ring','Pinky') for i in (1,2,3)]
pose={n:rig.pose.bones[n].matrix_basis.copy() for n in names}
p=out/'original.json';assert not p.exists();p.write_text(json.dumps({'preserve_volume':volume,'pose':{n:[list(row) for row in m] for n,m in pose.items()}}))
f=root/'pipeline/review_v492_isolated_palm.py';report=[]
def render(label):
 hand.update_tag();rig.update_tag();bpy.context.view_layer.update()
 ev=hand.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
 try: assert all(math.isfinite(c) for v in me.vertices for c in v.co)
 finally: ev.to_mesh_clear()
 s=f.read_text().replace('production_v492_palm_review','production_v514_right_skinning/'+label).replace('out.mkdir(exist_ok=True)','out.mkdir(parents=True,exist_ok=True)')
 exec(compile(s,str(f),'exec'),{'__file__':str(f)})
 report.append(label)
try:
 render('baseline_playing')
 mod.use_deform_preserve_volume=False;render('linear_playing')
 for n in names:rig.pose.bones[n].rotation_euler.x=0
 render('linear_open')
 mod.use_deform_preserve_volume=volume;render('baseline_open')
finally:
 mod.use_deform_preserve_volume=volume
 for n,m in pose.items():rig.pose.bones[n].matrix_basis=m
 rig.update_tag();hand.update_tag();bpy.context.view_layer.update()
 assert len(rig.animation_data.drivers)==1957
 (out/'report.json').write_text(json.dumps({'rendered':report,'restored':True,'drivers':1957}))
print('V514 compared linear and preserve-volume; original restored')
