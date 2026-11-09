"""Compare posed-cage subdivision; restore modifier order after rendering."""
import bpy,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
out=root/'production_v493_deform_order';out.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
hand=bpy.data.objects['V357_ANATOMICAL_HAND.R']
order=[m.name for m in hand.modifiers]
assert [m.type for m in hand.modifiers]==['MULTIRES','ARMATURE']
(out/'original_order.json').write_text(json.dumps(order))
try:
 hand.modifiers.move(1,0)
 bpy.context.view_layer.update()
 f=root/'pipeline/review_v492_isolated_palm.py'
 source=f.read_text().replace('production_v492_palm_review','production_v493_deform_order')
 exec(compile(source,str(f),'exec'),{'__file__':str(f)})
 f=root/'pipeline/check_v458_grip_fit.py'
 exec(compile(f.read_text().replace('production_v458_grip_fit/check.json','production_v493_deform_order/clearance.json'),str(f),'exec'),{})
finally:
 for i,name in enumerate(order):hand.modifiers.move(hand.modifiers.find(name),i)
 bpy.context.view_layer.update()
 assert [m.name for m in hand.modifiers]==order
 (out/'restored.json').write_text(json.dumps({'restored_order':order,'source':bpy.data.filepath}))
print('Trial rendered; original modifier order restored')
