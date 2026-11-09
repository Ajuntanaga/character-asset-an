"""Isolate scan underlay before editing the fiber groom."""
import bpy,json
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'production_v485_hair_isolation';out.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
g=bpy.data.objects['V449_CURL_GROOM']
p=out/'visibility.json'
assert not p.exists(), 'Existing trial must be restored first'
p.write_text(json.dumps({'render':g.hide_render,'viewport':g.hide_get()}))
g.hide_render=True
(root/'pipeline/render_preview_request.json').write_text(json.dumps({'output':'production_v485_hair_isolation/underlay.png','resolution':[700,800],'samples':24,'scale':.46,'camera':[.1,-2,1.67],'target':[0,0,1.65]}))
f=root/'pipeline/render_preview_job.py';exec(compile(f.read_text(),str(f),'exec'),dict(globals(),__file__=str(f)))
