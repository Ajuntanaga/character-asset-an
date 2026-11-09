import bpy,json
from pathlib import Path
from mathutils import Matrix,Vector
root=Path(__file__).resolve().parents[1];out=root/'production_v482_joint_width'
assert not bpy.app.is_job_running('RENDER')
r=bpy.data.objects['V357_CLOUDRIG_CONTROLS']
for name,m in json.loads((out/'original_pose.json').read_text()).items():r.pose.bones[name].matrix_basis=Matrix(m)
r.update_tag();bpy.context.view_layer.update();assert len(r.animation_data.drivers)==1957
path=out/'Character_An_joint_width_v482.blend';assert not path.exists()
bpy.ops.wm.save_as_mainfile(filepath=str(path))
g=bpy.data.objects['V206_GUITAR_ROOT'];cam=g.matrix_world@Vector((.68,.28,.42));target=g.matrix_world@Vector((.635,-.02,.045))
(root/'pipeline/render_preview_request.json').write_text(json.dumps({'output':'production_v482_joint_width/playing.png','resolution':[800,700],'samples':24,'scale':.30,'camera':list(cam),'target':list(target)}))
p=root/'pipeline/render_preview_job.py';exec(compile(p.read_text(),str(p),'exec'),dict(globals(),__file__=str(p)))
