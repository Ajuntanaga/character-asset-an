import bpy,json,math
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'production_v506_proximal_curl'
assert not bpy.app.is_job_running('RENDER')
r=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];assert len(r.animation_data.drivers)==1957
counts={}
for side in ('L','R'):
 h=bpy.data.objects['V357_ANATOMICAL_HAND.'+side];e=h.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh()
 try:
  assert all(math.isfinite(c) for v in m.vertices for c in v.co)
  counts[side]=len(m.vertices)
 finally:e.to_mesh_clear()
p=out/'Character_An_proximal_curl_candidate_v506.blend';assert not p.exists()
bpy.ops.wm.save_as_mainfile(filepath=str(p))
(out/'status.json').write_text(json.dumps({'saved':str(p),'vertices':counts,'drivers':1957,'accepted_grip':False,'angles_MRP':[[40,60,25],[45,60,25],[50,60,25]],'remaining':'String clearance -1.074mm including sampling buffer; no centreline crossings. Thumb/index/pick placement unresolved. Soft hand anatomy, left fretting, face/hair and character quality unfinished.'},indent=2))
print(str(p))
