import bpy,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
assert not bpy.app.is_job_running('RENDER')
for name in ('V485_CURL_GROOM','V486_CURL_GROOM'):
 obj=bpy.data.objects.get(name)
 if obj:
  data=obj.data;bpy.data.objects.remove(obj,do_unlink=True)
  if data.users==0:bpy.data.hair_curves.remove(data)
old=bpy.data.objects['V449_CURL_GROOM']
v=json.loads((root/'production_v485_hair_isolation/visibility.json').read_text())
old.hide_render=v['render'];old.hide_set(v['viewport'])
r=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];assert len(r.animation_data.drivers)==1957
report={'restored':'V449_CURL_GROOM','drivers':1957,'trial_status':'REJECTED','file':bpy.data.filepath}
(root/'production_v486_swept_curls/restored.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
