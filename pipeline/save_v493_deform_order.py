import bpy,json
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'production_v493_deform_order'
assert not bpy.app.is_job_running('RENDER')
assert 'v491' in bpy.data.filepath
hand=bpy.data.objects['V357_ANATOMICAL_HAND.R']
assert [m.type for m in hand.modifiers]==['MULTIRES','ARMATURE']
destination=out/'Character_An_hand_deform_order_v493.blend';assert not destination.exists()
hand.modifiers.move(1,0);bpy.context.view_layer.update()
f=root/'pipeline/check_v458_grip_fit.py'
exec(compile(f.read_text().replace('production_v458_grip_fit/check.json','production_v493_deform_order/saved_check.json'),str(f),'exec'),{})
check=json.loads((out/'saved_check.json').read_text())
assert check['finite'] and check['drivers']==1957 and not check['crossed_string_centrelines'] and check['sampled_clearance_m']>.0003
bpy.ops.wm.save_as_mainfile(filepath=str(destination))
(out/'status.json').write_text(json.dumps({'file':str(destination),'change':'Right hand Armature before Multires','review':'Open and curled palmar views show reduced thumb web pinch; curled dorsal view inspected','limits':['Anatomy still too smooth','Left hand unchanged and fret contact unresolved','Self collision not established'],'drivers':1957},indent=2))
print(str(destination))
