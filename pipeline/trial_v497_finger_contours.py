"""Shape inter-joint shaft contours without changing lengths, nails or rig."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1];out=root/'production_v497_finger_contours';out.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER') and 'v495' in bpy.data.filepath
backup=out/'original_coordinates.json';assert not backup.exists()
bones=json.loads((root/'production_v359_hand_weights/rest_hand_data.json').read_text())['bones']
backup.write_text(json.dumps({s:[list(v.co) for v in bpy.data.objects['V357_ANATOMICAL_HAND.'+s].data.vertices] for s in ('L','R')}))
report={}
for side in ('L','R'):
 obj=bpy.data.objects['V357_ANATOMICAL_HAND.'+side]
 nails={i for p in obj.data.polygons if p.material_index==1 for i in p.vertices}
 changes=[]
 for v in obj.data.vertices:
  if v.index in nails:continue
  co=v.co.copy();delta=Vector()
  for g in v.groups:
   name=obj.vertex_groups[g.group].name.replace('.R','.L')
   if name not in bones or not any('Finger_'+f in name for f in ('Index','Middle','Ring','Pinky')) or name.endswith('3.L'):continue
   a=Vector(bones[name]['head']);b=Vector(bones[name]['tail']);axis=b-a
   t=(co-a).dot(axis)/axis.length_squared
   if not 0<t<1:continue
   radial=co-(a+t*axis);fall=math.sin(math.pi*t)**2*g.weight
   delta.x-=radial.x*.13*fall
   if radial.y<0:delta.y-=radial.y*.05*fall
  if delta.length>1e-7:v.co+=delta;changes.append(delta.length)
 obj.data.update();obj.update_tag()
 report[side]={'changed':len(changes),'max_mm':max(changes)*1000}
bpy.context.view_layer.update()
report['drivers']=len(bpy.data.objects['V357_CLOUDRIG_CONTROLS'].animation_data.drivers);assert report['drivers']==1957
(out/'changes.json').write_text(json.dumps(report,indent=2))
f=root/'pipeline/review_v496_rest_shape.py'
s=f.read_text().replace('production_v496_rest_shape','production_v497_finger_contours/rest')
# The nested helper creates its own output directory.
s=s.replace("s=f.read_text().replace(","s=f.read_text().replace('out.mkdir(exist_ok=True)','out.mkdir(parents=True,exist_ok=True)').replace(")
exec(compile(s,str(f),'exec'),{'__file__':str(f)})
f=root/'pipeline/review_v492_isolated_palm.py'
s=f.read_text().replace('production_v492_palm_review','production_v497_finger_contours/playing').replace('out.mkdir(exist_ok=True)','out.mkdir(parents=True,exist_ok=True)')
exec(compile(s,str(f),'exec'),{'__file__':str(f)})
print(json.dumps(report))
