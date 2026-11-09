import bpy,json,math
from pathlib import Path
from mathutils import Matrix
root=Path(__file__).resolve().parents[1];out=root/'production_v511_lateral_pick';out.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
r=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];pick=bpy.data.objects['V361_NYLON_PICK'];assert len(r.animation_data.drivers)==1957
bones=[r.pose.bones[f'FK-Finger_Index{i}.R'] for i in (1,2,3)]
backup=out/'original_pose.json';assert not backup.exists()
original={b.name:[list(row) for row in b.matrix_basis] for b in bones};original_pick=pick.matrix_world.copy()
backup.write_text(json.dumps({'bones':original,'pick':[list(row) for row in original_pick]}))
try:
 for b,a in zip(bones,(45,55,8)):b.rotation_euler.x=math.radians(a)
 # Spread index away from curled middle while retaining a mild distal bend.
 bones[0].rotation_euler.z+=math.radians(10)
 r.update_tag();bpy.context.view_layer.update()
 f=root/'pipeline/inspect_v503_pick_frame.py'
 exec(compile(f.read_text().replace('production_v503_pick_seating','production_v511_lateral_pick'),str(f),'exec'),{'__file__':str(f)})
 f=root/'pipeline/trial_v503_pick_seating.py'
 exec(compile(f.read_text().replace('production_v503_pick_seating','production_v511_lateral_pick'),str(f),'exec'),{'__file__':str(f)})
 (out/'trial_pose.json').write_text(json.dumps({'bones':{b.name:[list(row) for row in b.matrix_basis] for b in bones},'pick':[list(row) for row in pick.matrix_world]}))
 f=root/'pipeline/inspect_v510_grip.py'
 exec(compile(f.read_text().replace('production_v510_grip_review','production_v511_lateral_pick'),str(f),'exec'),{'__file__':str(f)})
 f=root/'pipeline/check_v458_grip_fit.py'
 exec(compile(f.read_text().replace('production_v458_grip_fit/check.json','production_v511_lateral_pick/check.json'),str(f),'exec'),{'__file__':str(f)})
finally:
 for n,m in original.items():r.pose.bones[n].matrix_basis=Matrix(m)
 r.update_tag();bpy.context.view_layer.update();pick.matrix_world=original_pick;bpy.context.view_layer.update()
 assert len(r.animation_data.drivers)==1957
 (out/'restored.json').write_text(json.dumps({'restored':True,'drivers':1957}))
print('V511 finished; original hand and pick restored')
