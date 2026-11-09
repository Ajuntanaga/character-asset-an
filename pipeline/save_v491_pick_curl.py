import bpy,json
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'production_v491_pick_curl'
assert not bpy.app.is_job_running('RENDER')
assert 'v490' in bpy.data.filepath
r=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];assert len(r.animation_data.drivers)==1957
f=root/'pipeline/check_v458_grip_fit.py';exec(compile(f.read_text().replace('production_v458_grip_fit/check.json','production_v491_pick_curl/saved_check.json'),str(f),'exec'),{})
check=json.loads((out/'saved_check.json').read_text());assert check['finite'] and not check['crossed_string_centrelines'] and check['sampled_clearance_m']>.0003
p=out/'Character_An_pick_curl_candidate_v491.blend';assert not p.exists()
bpy.ops.wm.save_as_mainfile(filepath=str(p))
(out/'status.json').write_text(json.dumps({'status':'POSE_CANDIDATE_NOT_ANATOMY_ACCEPTANCE','drivers':1957,'file':str(p),'limits':['Rounded knuckles','Pinched web deformation','No palm-side visual review or self-collision certification','Left fretting unresolved']},indent=2));print(str(p))
