import bpy,json
from pathlib import Path
from mathutils import Matrix
root=Path(__file__).resolve().parents[1];out=root/'production_v509_loose_pick_pose'
assert not bpy.app.is_job_running('RENDER')
r=bpy.data.objects['V357_CLOUDRIG_CONTROLS']
backup=json.loads((out/'original_pose.json').read_text())
for n,m in backup.items():r.pose.bones[n].matrix_basis=Matrix(m)
r.update_tag();bpy.context.view_layer.update()
assert len(r.animation_data.drivers)==1957
assert max(abs(r.pose.bones[n].matrix_basis[i][j]-m[i][j]) for n,m in backup.items() for i in range(4) for j in range(4))<1e-5
(out/'status.json').write_text(json.dumps({'accepted':False,'restored':'V508 pose','drivers':1957,'reason':'Loose pose intersects strings; clearance-safe sweep pose creates dangling middle finger inconsistent with reference. Do not retain as playing grip.'},indent=2))
print('V508 pose restored;1957drivers preserved')
