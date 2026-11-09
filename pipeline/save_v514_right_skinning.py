"""Retain reviewed right linear skinning if playing-string check passes."""
import bpy,json
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'production_v514_right_skinning'
assert not bpy.app.is_job_running('RENDER') and 'v508' in bpy.data.filepath
hand=bpy.data.objects['V357_ANATOMICAL_HAND.R'];mod=next(m for m in hand.modifiers if m.type=='ARMATURE')
assert mod.use_deform_preserve_volume
path=out/'Character_An_bilateral_linear_skinning_v514.blend';assert not path.exists()
mod.use_deform_preserve_volume=False;hand.update_tag();bpy.context.view_layer.update()
try:
 f=root/'pipeline/check_v458_grip_fit.py'
 s=f.read_text().replace('production_v458_grip_fit/check.json','production_v514_right_skinning/check.json')
 exec(compile(s,str(f),'exec'),{'__file__':str(f)})
 check=json.loads((out/'check.json').read_text())
 assert check['finite'] and check['drivers']==1957 and not check['crossed_string_centrelines'] and check['sampled_clearance_m']>0
 bpy.ops.wm.save_as_mainfile(filepath=str(path))
 (out/'saved.json').write_text(json.dumps({'file':bpy.data.filepath,'drivers':1957,'right_preserve_volume':False,'review':'Reduced thumb web fold; finger anatomy and pinch remain unfinished.'},indent=2))
except Exception:
 mod.use_deform_preserve_volume=True;hand.update_tag();bpy.context.view_layer.update();raise
print('V514 saved separately')
