import bpy,json,math
from pathlib import Path
root=Path(__file__).resolve().parents[1]
out=root/'production_v508_hand_surface'
assert not bpy.app.is_job_running('RENDER')
r=bpy.data.objects['V357_CLOUDRIG_CONTROLS']
assert len(r.animation_data.drivers)==1957
for side in ('L','R'):
    obj=bpy.data.objects['V357_ANATOMICAL_HAND.'+side]
    assert obj.data.materials[0].name.startswith('V508_Mature_Hand_Surface.')
    ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh=ev.to_mesh()
    try:
        assert all(math.isfinite(c) for v in mesh.vertices for c in v.co)
    finally:
        ev.to_mesh_clear()
p=out/'Character_An_hand_surface_candidate_v508.blend'
assert not p.exists()
bpy.ops.wm.save_as_mainfile(filepath=str(p))
(out/'status.json').write_text(json.dumps({'saved':str(p),'drivers':1957,'finite_hands':True,'accepted_anatomy':False,'assessment':'Modest surface variation only; broad palm, soft joints, curled finger proportions and pick contact unresolved.'},indent=2))
print(str(p))
