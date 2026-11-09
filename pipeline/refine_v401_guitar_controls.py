"""Reduce oversized guitar knobs to reference-like proportions."""
from pathlib import Path
import json,bpy
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'production_v401_guitar_controls';OUT.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
rig=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];assert len(rig.animation_data.drivers)==1957
report={}
for i in (1,2):
 o=bpy.data.objects[f'V206_CONTROL_KNOB_{i}']
 assert not o.get('V401_resize')
 report[o.name]={'before_dimensions':list(o.dimensions),'before_location':list(o.location)}
 for v in o.data.vertices:
  v.co.x*=24/31;v.co.y*=24/31;v.co.z*=14/18
 o.location.z-=.002
 o.data.update();o['V401_resize']=True
 report[o.name]['target_dimensions']=[.024,.024,.014]
(OUT/'report.json').write_text(json.dumps(report,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Character_An_guitar_controls_v401.blend'),compress=True)
print(json.dumps(report))
