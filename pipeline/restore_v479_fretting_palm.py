import bpy,json
from pathlib import Path
from mathutils import Matrix
root=Path(__file__).resolve().parents[1];out=root/'production_v479_fretting_palm'
assert not bpy.app.is_job_running('RENDER')
assert not (out/'restored.json').exists()
r=bpy.data.objects['V357_CLOUDRIG_CONTROLS']
for n,m in json.loads((out/'original_pose.json').read_text()).items():r.pose.bones[n].matrix_basis=Matrix(m)
r.update_tag();bpy.context.view_layer.update()
assert len(r.animation_data.drivers)==1957
(out/'restored.json').write_text(json.dumps({'restored':True,'drivers':1957,'saved_file':bpy.data.filepath}))
print((out/'restored.json').read_text())
