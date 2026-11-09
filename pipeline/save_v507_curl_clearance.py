import bpy,json,math
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'production_v507_curl_clearance'
assert not bpy.app.is_job_running('RENDER')
r=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];assert len(r.animation_data.drivers)==1957
check=json.loads((out/'check.json').read_text());assert check['finite'] and not check['crossed_string_centrelines'] and check['sampled_clearance_m']>.0003
p=out/'Character_An_curl_clearance_candidate_v507.blend';assert not p.exists();bpy.ops.wm.save_as_mainfile(filepath=str(p))
(out/'status.json').write_text(json.dumps({'saved':str(p),'drivers':1957,'accepted_grip':False,'clearance_m':check['sampled_clearance_m'],'remaining':'Thumb/index/pick fit, hand anatomy and skin, fretting, face/hair, full character and animation acceptance remain unfinished.'},indent=2));print(str(p))
