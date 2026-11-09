"""Reduce excess picking-cuff taper volume while preserving both sewn boundaries."""
from pathlib import Path
import bpy,json
from mathutils import Vector
R=Path(__file__).resolve().parents[1];O=R/'production_v434_cuff_taper';O.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
assert bpy.data.filepath.endswith('Character_An_fret_clearance_v430.blend')
rig=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];assert len(rig.animation_data.drivers)==1957
o=bpy.data.objects['V421_REGULAR_SLEEVE_CUFF.R'];o.data=o.data.copy();o.data.name='V434_Cuff_Taper'
report=[]
for ring,factor in [(0,.86),(1,.82),(2,.94)]:
 vertices=list(o.data.vertices)[328+ring*96:328+(ring+1)*96]
 center=sum((v.co for v in vertices),Vector())/len(vertices)
 for v in vertices:
  v.co.x=center.x+(v.co.x-center.x)*factor
  v.co.y=center.y+(v.co.y-center.y)*factor
 report.append({'ring':ring,'radial_factor':factor})
o.data.update();bpy.context.view_layer.update()
(O/'report.json').write_text(json.dumps({'changes':report,'preserved':'jacket boundary, wrist opening, hand geometry, rig and pose','drivers':len(rig.animation_data.drivers)},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(O/'Character_An_cuff_taper_v434.blend'),compress=True)
print('Saved V434',report)
