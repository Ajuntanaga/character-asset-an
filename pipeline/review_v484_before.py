import bpy,json
from pathlib import Path
from mathutils import Matrix
root=Path(__file__).resolve().parents[1];out=root/'production_v484_finger_length';r=bpy.data.objects['V357_CLOUDRIG_CONTROLS']
assert not bpy.app.is_job_running('RENDER')
for n,m in json.loads((out/'original_pose.json').read_text()).items():r.pose.bones[n].matrix_basis=Matrix(m)
r.update_tag();bpy.context.view_layer.update()
p=root/'pipeline/render_preview_request.json';q=json.loads(p.read_text());q['output']='production_v484_finger_length/before.png';p.write_text(json.dumps(q))
f=root/'pipeline/render_preview_job.py';exec(compile(f.read_text(),str(f),'exec'),dict(globals(),__file__=str(f)))
