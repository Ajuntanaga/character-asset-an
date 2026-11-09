import bpy,json
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];r=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];report=[]
for item in json.loads((R/'production_v406_pick_relax/string_contact.json').read_text()):
 for hit in item['centerline_crossings']:
  p=Vector(hit['point']);near=[]
  for b in r.pose.bones:
   if not b.name.startswith('DEF-Finger_') or not b.name.endswith('.R'):continue
   a=r.matrix_world@b.head;c=r.matrix_world@b.tail;d=c-a;t=max(0,min(1,(p-a).dot(d)/max(d.length_squared,1e-12)))
   near.append(((p-(a+t*d)).length,b.name))
  report.append({'string':item['string'],'nearest_bones':sorted(near)[:5]})
print(json.dumps(report));(R/'production_v406_pick_relax/contact_bones.json').write_text(json.dumps(report,indent=2))
