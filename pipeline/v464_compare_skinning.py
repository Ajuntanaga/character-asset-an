import bpy,json
from pathlib import Path
root=Path('/home/ajuntanaga/Projects/Blender/Character Asset_An')
out=root/'production_v464_linear_deformation';out.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
original={}
for side in ('L','R'):
 o=bpy.data.objects['V357_ANATOMICAL_HAND.'+side]
 for m in o.modifiers:
  if m.type=='ARMATURE':
   original[o.name]=m.use_deform_preserve_volume
   m.use_deform_preserve_volume=False
(out/'original_modifier.json').write_text(json.dumps(original))
(out/'mode.txt').write_text('curl')
p=root/'pipeline/check_v462_hand_deformation.py'
s=p.read_text().replace('production_v462_hand_deformation','production_v464_linear_deformation')
exec(compile(s,str(p),'exec'),dict(globals(),__file__=str(p)))
