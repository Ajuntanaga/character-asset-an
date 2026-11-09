import bpy,json,math
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'production_v497_finger_contours'
assert not bpy.app.is_job_running('RENDER') and 'v495' in bpy.data.filepath
f=root/'pipeline/check_v458_grip_fit.py'
s=f.read_text().replace('production_v458_grip_fit/check.json','production_v497_finger_contours/check.json')
exec(compile(s,str(f),'exec'),{'__file__':str(f)})
check=json.loads((out/'check.json').read_text())
assert check['finite'] and not check['crossed_string_centrelines'] and check['sampled_clearance_m']>0 and check['drivers']==1957
left=bpy.data.objects['V357_ANATOMICAL_HAND.L'].evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=left.to_mesh()
assert all(math.isfinite(x) for v in mesh.vertices for x in v.co)
left.to_mesh_clear()
p=out/'Character_An_finger_contours_v497.blend';assert not p.exists()
bpy.ops.wm.save_as_mainfile(filepath=str(p));print('V497 saved')
