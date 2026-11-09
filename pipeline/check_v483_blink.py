import bpy,json
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'production_v483_eye_rest'
assert not bpy.app.is_job_running('RENDER')
r=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];h=r.pose.bones['Head']
h['Blink.L']=h['Blink.R']=1.0
r.update_tag();bpy.context.view_layer.update();assert len(r.animation_data.drivers)==1957
(root/'pipeline/render_preview_request.json').write_text(json.dumps({'output':'production_v483_eye_rest/blink.png','resolution':[700,800],'samples':24,'scale':.46,'camera':[.1,-2,1.67],'target':[0,0,1.65]}))
p=root/'pipeline/render_preview_job.py';exec(compile(p.read_text(),str(p),'exec'),dict(globals(),__file__=str(p)))
