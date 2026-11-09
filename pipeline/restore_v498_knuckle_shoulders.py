import bpy,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
assert not bpy.app.is_job_running('RENDER') and 'v497' in bpy.data.filepath
backup=json.loads((root/'production_v498_knuckle_shoulders/original_coordinates.json').read_text())
for side,coords in backup.items():
 obj=bpy.data.objects['V357_ANATOMICAL_HAND.'+side];assert len(obj.data.vertices)==len(coords)
 for v,co in zip(obj.data.vertices,coords):v.co=co
 obj.data.update();obj.update_tag()
bpy.context.view_layer.update()
assert len(bpy.data.objects['V357_CLOUDRIG_CONTROLS'].animation_data.drivers)==1957
print('V498 rejected; V497 coordinates restored on both hands')
