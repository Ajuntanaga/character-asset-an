"""Shape inter-joint shaft contours without changing lengths, nails or rig."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1];out=root/'production_v499_finger_contours';out.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER') and 'v497' in bpy.data.filepath
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
   radial=co-(a+t*axis)
   # Flatten the dorsal crown into a broad joint plane rather than adding bumps.
   distance=min((co-a).length,(co-b).length)
   longitudinal=min(t,1-t)*axis.length
   joint=max(0,1-longitudinal/.012)**2
   if radial.y<-.003:
    crown=max(0,1-abs(radial.x)/.009)
    delta.y+=min(.0035,(-radial.y-.003)*.45)*crown*joint*g.weight
  if delta.length>1e-7:v.co+=delta;changes.append(delta.length)
 obj.data.update();obj.update_tag()
 report[side]={'changed':len(changes),'max_mm':max(changes)*1000}
bpy.context.view_layer.update()
report['drivers']=len(bpy.data.objects['V357_CLOUDRIG_CONTROLS'].animation_data.drivers);assert report['drivers']==1957
(out/'changes.json').write_text(json.dumps(report,indent=2))
f=root/'pipeline/review_v496_rest_shape.py'
s=f.read_text().replace("'v495'","'v497'").replace('production_v496_rest_shape','production_v499_finger_contours/rest')
# The nested helper creates its own output directory.
s=s.replace("s=f.read_text().replace(","s=f.read_text().replace('out.mkdir(exist_ok=True)','out.mkdir(parents=True,exist_ok=True)').replace(")
exec(compile(s,str(f),'exec'),{'__file__':str(f)})
f=root/'pipeline/review_v492_isolated_palm.py'
s=f.read_text().replace('production_v492_palm_review','production_v499_finger_contours/playing').replace('out.mkdir(exist_ok=True)','out.mkdir(parents=True,exist_ok=True)')
exec(compile(s,str(f),'exec'),{'__file__':str(f)})
print(json.dumps(report))
