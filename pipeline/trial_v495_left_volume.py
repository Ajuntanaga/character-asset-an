"""Isolate volume-preserving skinning contribution to the left palm bulge."""
import bpy,json
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'production_v495_left_volume';out.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER') and 'v494' in bpy.data.filepath
hand=bpy.data.objects['V357_ANATOMICAL_HAND.L'];mod=next(m for m in hand.modifiers if m.type=='ARMATURE')
original=mod.use_deform_preserve_volume
assert original
f=root/'pipeline/review_v492_isolated_palm.py'
source=f.read_text().replace('V357_ANATOMICAL_HAND.R','V357_ANATOMICAL_HAND.L').replace('DEF-Hand.R','DEF-Hand.L').replace('production_v492_palm_review','production_v495_left_volume')
try:
 mod.use_deform_preserve_volume=False;bpy.context.view_layer.update()
 exec(compile(source,str(f),'exec'),{'__file__':str(f)})
finally:
 mod.use_deform_preserve_volume=original;bpy.context.view_layer.update()
(out/'restored.json').write_text(json.dumps({'volume_preservation':mod.use_deform_preserve_volume,'file':bpy.data.filepath}))
print('Original volume preservation restored')
