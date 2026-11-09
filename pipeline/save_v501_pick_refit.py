import bpy,json,math
from pathlib import Path
root=Path('/home/ajuntanaga/Projects/Blender/Character Asset_An');out=root/'production_v501_pick_refit'
assert not bpy.app.is_job_running('RENDER')
r=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];assert len(r.animation_data.drivers)==1957
for side in ('L','R'):
 h=bpy.data.objects['V357_ANATOMICAL_HAND.'+side];e=h.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh()
 try:assert all(math.isfinite(c) for v in m.vertices for c in v.co)
 finally:e.to_mesh_clear()
check=json.loads((out/'final_check.json').read_text());assert not check['crossed_string_centrelines'] and check['sampled_clearance_m']>0
path=out/'Character_An_pick_refit_candidate_v501.blend';assert not path.exists();bpy.ops.wm.save_as_mainfile(filepath=str(path))
(out/'status.json').write_text(json.dumps({'saved':str(path),'drivers':1957,'accepted_grip':False,'remaining':'Thumb index gap approximately2.4mm; pick tip15.6mm above strings; anatomy and playing contact unresolved'},indent=2));print(str(path))
