import bpy,json
from pathlib import Path
from mathutils import Matrix
root=Path(__file__).resolve().parents[1];out=root/'production_v488_reference_pick_curl'
assert not bpy.app.is_job_running('RENDER')
rig=bpy.data.objects['V357_CLOUDRIG_CONTROLS']
backup=json.loads((out/'original_pose.json').read_text())
for n,m in backup.items():rig.pose.bones[n].matrix_basis=Matrix(m)
rig.update_tag();bpy.context.view_layer.update()
error=max(abs(rig.pose.bones[n].matrix_basis[i][j]-m[i][j]) for n,m in backup.items() for i in range(4) for j in range(4))
assert error<1e-6 and len(rig.animation_data.drivers)==1957
report={'restored':True,'max_matrix_error':error,'drivers':1957,'status':'REJECTED_CLEARANCE_AND_ANATOMY','saved_file':bpy.data.filepath}
(out/'restored.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
