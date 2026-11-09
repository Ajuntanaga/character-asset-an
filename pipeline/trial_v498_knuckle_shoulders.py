"""Add localized dorsal joint shoulders, retaining flatter central crowns."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1];out=root/'production_v498_knuckle_shoulders';out.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER') and 'v497' in bpy.data.filepath
backup=out/'original_coordinates.json';assert not backup.exists()
backup.write_text(json.dumps({s:[list(v.co) for v in bpy.data.objects['V357_ANATOMICAL_HAND.'+s].data.vertices] for s in ('L','R')}))
bones=json.loads((root/'production_v359_hand_weights/rest_hand_data.json').read_text())['bones'];report={}
for side in ('L','R'):
 obj=bpy.data.objects['V357_ANATOMICAL_HAND.'+side];nails={i for p in obj.data.polygons if p.material_index==1 for i in p.vertices};changes=[]
 for v in obj.data.vertices:
  if v.index in nails:continue
  co=v.co.copy();dy=0
  for g in v.groups:
   name=obj.vertex_groups[g.group].name.replace('.R','.L')
   if name not in bones or not any('Finger_'+f in name for f in ('Index','Middle','Ring','Pinky')):continue
   a=Vector(bones[name]['head']);b=Vector(bones[name]['tail']);axis=b-a
   t=(co-a).dot(axis)/axis.length_squared;radial=co-(a+t*axis)
   if radial.y>=-.002:continue
   end=(math.exp(-((t*axis.length)/.006)**2)+math.exp(-(((1-t)*axis.length)/.006)**2))
   shoulders=math.exp(-((abs(radial.x)-.0045)/.003)**2)
   dy-=.0012*min(1,end)*shoulders*min(1,(-radial.y-.002)/.004)*g.weight
  if abs(dy)>1e-7:v.co.y+=dy;changes.append(abs(dy))
 obj.data.update();obj.update_tag();report[side]={'changed':len(changes),'max_mm':max(changes)*1000}
bpy.context.view_layer.update();report['drivers']=len(bpy.data.objects['V357_CLOUDRIG_CONTROLS'].animation_data.drivers);assert report['drivers']==1957
(out/'changes.json').write_text(json.dumps(report,indent=2))
f=root/'pipeline/review_v496_rest_shape.py'
s=f.read_text().replace("'v495'","'v497'").replace('production_v496_rest_shape','production_v498_knuckle_shoulders/rest')
s=s.replace("s=f.read_text().replace(","s=f.read_text().replace('out.mkdir(exist_ok=True)','out.mkdir(parents=True,exist_ok=True)').replace(")
exec(compile(s,str(f),'exec'),{'__file__':str(f)})
f=root/'pipeline/review_v492_isolated_palm.py'
s=f.read_text().replace('production_v492_palm_review','production_v498_knuckle_shoulders/playing').replace('out.mkdir(exist_ok=True)','out.mkdir(parents=True,exist_ok=True)')
exec(compile(s,str(f),'exec'),{'__file__':str(f)})
print(json.dumps(report))
