import bpy,json,math
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1];out=root/'production_v505_web_recess';out.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
backup=out/'original_coordinates.json';assert not backup.exists()
backup.write_text(json.dumps({s:[list(v.co) for v in bpy.data.objects['V357_ANATOMICAL_HAND.'+s].data.vertices] for s in ('L','R')}))
# Actual cross-digit bridge edges, measured in the common hand-mesh local frame.
seeds=[(147,564),(735,736),(108,567)];report={}
for side in ('L','R'):
 o=bpy.data.objects['V357_ANATOMICAL_HAND.'+side];centers=[(o.data.vertices[a].co+o.data.vertices[b].co)*.5 for a,b in seeds];nails={i for p in o.data.polygons if p.material_index==1 for i in p.vertices};deltas=[]
 for v in o.data.vertices:
  if v.index in nails:continue
  weights={o.vertex_groups[w.group].name:w.weight for w in v.groups}
  if any(('Thumb' in n or n.endswith(('2.'+side,'3.'+side))) and w>.001 for n,w in weights.items()):continue
  c=v.co.copy();fall=max(math.exp(-((c.x-q.x)/.0075)**2-((c.z-q.z)/.012)**2) for q in centers)
  if fall<.02:continue
  dz=.006*fall;v.co.z+=dz;deltas.append(dz)
 o.data.update();o.update_tag();report[side]={'changed':len(deltas),'maximum_mm':max(deltas)*1000}
bpy.context.view_layer.update();assert len(bpy.data.objects['V357_CLOUDRIG_CONTROLS'].animation_data.drivers)==1957
(out/'changes.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
f=root/'pipeline/review_v496_rest_shape.py';s=f.read_text().replace(" and 'v495' in bpy.data.filepath",'').replace('production_v496_rest_shape','production_v505_web_recess/rest').replace("s=f.read_text().replace(","s=f.read_text().replace('out.mkdir(exist_ok=True)','out.mkdir(parents=True,exist_ok=True)').replace(")
exec(compile(s,str(f),'exec'),{'__file__':str(f)})
f=root/'pipeline/review_v492_isolated_palm.py';s=f.read_text().replace('production_v492_palm_review','production_v505_web_recess/playing').replace('out.mkdir(exist_ok=True)','out.mkdir(parents=True,exist_ok=True)');exec(compile(s,str(f),'exec'),{'__file__':str(f)})
