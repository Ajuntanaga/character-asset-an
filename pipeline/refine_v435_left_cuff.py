"""Tailor the fretting cuff midsection, retaining its sewn edge and wrist hem."""
import bpy,json,math
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'production_v435_left_cuff';O.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
assert bpy.data.filepath.endswith('Character_An_cuff_taper_v434.blend')
r=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];assert len(r.animation_data.drivers)==1957
o=bpy.data.objects['V357_CUFF_PATCH.L'];o.data=o.data.copy();o.data.name='V435_Tailored_Left_Cuff'
changed=0;maximum=0
for v in o.data.vertices:
 z=v.co.z
 if not .881<z<.933:continue
 t=(z-.881)/.052;weight=math.sin(math.pi*t)**2;factor=1-.22*weight
 old=v.co.copy();v.co.x=.298+(v.co.x-.298)*factor;v.co.y=.020+(v.co.y-.020)*factor
 maximum=max(maximum,(v.co-old).length);changed+=1
o.data.update();bpy.context.view_layer.update()
(O/'report.json').write_text(json.dumps({'vertices_changed':changed,'max_displacement_m':maximum,'drivers':len(r.animation_data.drivers),'preserved':'wrist hem, upper sewn boundary, hand pose and geometry'},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(O/'Character_An_left_cuff_v435.blend'),compress=True)
print('V435 saved',changed,maximum)
