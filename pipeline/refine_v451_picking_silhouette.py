"""Relax unused picking fingers; retain thumb/index pinch and wrist transform."""
import bpy,json,math
from pathlib import Path
root=Path(__file__).resolve().parents[1]
assert 'v449' in bpy.data.filepath
assert not bpy.app.is_job_running('RENDER')
r=bpy.data.objects['V357_CLOUDRIG_CONTROLS']
assert len(r.animation_data.drivers)==1957
out=root/'production_v451_picking_silhouette';out.mkdir(exist_ok=True)
changes=[]
for digit,angles in [('Middle',(25,48,22)),('Ring',(30,54,25)),('Pinky',(35,60,28))]:
 for joint,angle in enumerate(angles,1):
  b=r.pose.bones[f'FK-Finger_{digit}{joint}.R']
  before=list(b.rotation_euler);b.rotation_euler.x=math.radians(angle)
  changes.append({'bone':b.name,'before':before,'after':list(b.rotation_euler)})
r.update_tag();bpy.context.view_layer.update()
(out/'changes.json').write_text(json.dumps(changes,indent=2))
print(json.dumps({'changes':changes,'drivers':len(r.animation_data.drivers)}))
