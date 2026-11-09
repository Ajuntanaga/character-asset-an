import bpy,json,math
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'production_v490_hand_anatomy'
assert not bpy.app.is_job_running('RENDER')
# Restore review controls, then original playing curl (review started in stress pose).
(out/'mode.txt').write_text('restore')
f=root/'pipeline/check_v472_hand_deformation.py';s=f.read_text().replace('production_v472_hand_deformation','production_v490_hand_anatomy');exec(compile(s,str(f),'exec'),dict(globals(),__file__=str(f)))
f=root/'pipeline/restore_v488_pick_curl.py';exec(compile(f.read_text(),str(f),'exec'),dict(globals(),__file__=str(f)))
report={}
for side in ('L','R'):
 e=bpy.data.objects['V357_ANATOMICAL_HAND.'+side].evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh()
 try:report[side]={'finite':all(math.isfinite(c) for v in m.vertices for c in v.co),'vertices':len(m.vertices)}
 finally:e.to_mesh_clear()
assert all(v['finite'] for v in report.values())
report['drivers']=len(bpy.data.objects['V357_CLOUDRIG_CONTROLS'].animation_data.drivers);assert report['drivers']==1957
p=out/'Character_An_hand_anatomy_candidate_v490.blend';assert not p.exists()
bpy.ops.wm.save_as_mainfile(filepath=str(p))
report['status']='ANATOMY_CANDIDATE_NOT_PRODUCTION_ACCEPTANCE';(out/'saved.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
