import bpy,json
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1];out=root/'production_v484_finger_length'
assert not bpy.app.is_job_running('RENDER')
r=bpy.data.objects['V357_CLOUDRIG_CONTROLS']
backup=json.loads((out/'original_pose.json').read_text())
for n in backup:
 if n.split('.')[0].endswith('1'):r.pose.bones[n].scale.y*=1.12
r.update_tag();bpy.context.view_layer.update()
report={n:r.pose.bones[n.replace('FK-','DEF-')].length for n in backup}
(out/'corrected_lengths.json').write_text(json.dumps(report,indent=2))
g=bpy.data.objects.get('V356_GUITAR_ROOT')
print('guitar',g.name if g else None)
(root/'pipeline/render_preview_request.json').write_text(json.dumps({'output':'production_v484_finger_length/corrected.png','resolution':[1000,900],'samples':24,'scale':.66,'camera':[.10,-2,1.20],'target':[0,-.26,1.10]}))
f=root/'pipeline/render_preview_job.py';exec(compile(f.read_text(),str(f),'exec'),dict(globals(),__file__=str(f)))
