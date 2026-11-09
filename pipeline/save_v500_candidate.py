import bpy,json,math
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'production_v500_finger_proportions'
assert not bpy.app.is_job_running('RENDER') and 'v497' in bpy.data.filepath
f=root/'pipeline/check_v458_grip_fit.py'
s=f.read_text().replace('production_v458_grip_fit/check.json','production_v500_finger_proportions/check.json')
exec(compile(s,str(f),'exec'),{'__file__':str(f)})
check=json.loads((out/'check.json').read_text())
assert check['finite'] and check['drivers']==1957
left=bpy.data.objects['V357_ANATOMICAL_HAND.L'].evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=left.to_mesh()
assert all(math.isfinite(x) for v in mesh.vertices for x in v.co)
left.to_mesh_clear()
p=out/'Character_An_proportion_candidate_v500.blend';assert not p.exists()
bpy.ops.wm.save_as_mainfile(filepath=str(p));print('V500 proportion WIP saved; clearance result retained, not contact acceptance')
