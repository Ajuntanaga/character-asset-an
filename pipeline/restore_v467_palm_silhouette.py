import bpy,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
assert not bpy.app.is_job_running('RENDER')
h=bpy.data.objects['V357_ANATOMICAL_HAND.R']
for v,co in zip(h.data.vertices,json.loads((root/'production_v467_palm_silhouette/coordinates.json').read_text())):v.co=co
h.data.update();h.update_tag();bpy.context.view_layer.update()
assert len(bpy.data.objects['V357_CLOUDRIG_CONTROLS'].animation_data.drivers)==1957
print('V466 palm restored; V467 rejected; no production save')
