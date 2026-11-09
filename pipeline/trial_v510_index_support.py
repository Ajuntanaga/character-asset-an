import bpy,json,math
from pathlib import Path
from mathutils import Matrix
root=Path(__file__).resolve().parents[1];out=root/'production_v510_index_support';out.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
r=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];assert len(r.animation_data.drivers)==1957
bones=[r.pose.bones[f'FK-Finger_Index{i}.R'] for i in (1,2,3)]
backup=out/'original_pose.json';assert not backup.exists()
backup.write_text(json.dumps({b.name:[list(row) for row in b.matrix_basis] for b in bones}))
try:
 # Move bend toward MCP, reduce hooked PIP; retain spread and twist.
 for b,a in zip(bones,(45,55,8)):b.rotation_euler.x=math.radians(a)
 r.update_tag();bpy.context.view_layer.update()
 f=root/'pipeline/inspect_v510_grip.py'
 s=f.read_text().replace('production_v510_grip_review','production_v510_index_support')
 exec(compile(s,str(f),'exec'),{'__file__':str(f)})
 (out/'trial_pose.json').write_text(json.dumps({b.name:[list(row) for row in b.matrix_basis] for b in bones}))
finally:
 for n,m in json.loads(backup.read_text()).items():r.pose.bones[n].matrix_basis=Matrix(m)
 r.update_tag();bpy.context.view_layer.update()
 assert len(r.animation_data.drivers)==1957
 (out/'restored.json').write_text(json.dumps({'restored':True,'drivers':1957,'saved_candidate':False}))
print('V510 comparison complete; original index pose restored')
