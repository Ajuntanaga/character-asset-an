import bpy,json,math
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1];out=root/'production_v470_face_proportions';out.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
r=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];assert len(r.animation_data.drivers)==1957
backup={};report={}
def smooth(t):
 t=max(0,min(1,t));return t*t*(3-2*t)
for name in ('V416_BODY_CLEAN_JOIN','V395_BEARD_FIBERS','V363_LIPS'):
 o=bpy.data.objects[name];keys=o.data.shape_keys.key_blocks;basis=keys['Basis'];ids=set(range(len(basis.data)))
 if name=='V416_BODY_CLEAN_JOIN':
  ids={v for p in o.data.polygons if p.material_index in (0,4,5) for v in p.vertices}
 changed={};maximum=0
 for i in ids:
  p=o.matrix_world@basis.data[i].co
  if p.z<1.475 or p.z>1.65 or p.y>.015:continue
  envelope=smooth((p.z-1.475)/.055)*smooth((1.65-p.z)/.065)
  side=smooth((abs(p.x)-.025)/.035)
  dx=-p.x*.085*envelope*side
  dz=-.006*smooth((p.z-1.475)/.045)*smooth((1.61-p.z)/.07)
  delta=o.matrix_world.inverted().to_3x3()@Vector((dx,0,dz))
  if delta.length<1e-8:continue
  changed[str(i)]=list(delta);maximum=max(maximum,delta.length)
  for key in keys:key.data[i].co+=delta
 o.data.update();backup[name]=changed;report[name]={'vertices':len(changed),'max_delta_mm':maximum*1000}
(out/'deltas.json').write_text(json.dumps(backup));(out/'report.json').write_text(json.dumps(report,indent=2));r.update_tag();bpy.context.view_layer.update();print(json.dumps(report))
req={'output':'production_v470_face_proportions/face.png','resolution':[700,800],'samples':32,'scale':.46,'camera':[.1,-2,1.67],'target':[0,0,1.65]}
(root/'pipeline/render_preview_request.json').write_text(json.dumps(req));f=root/'pipeline/render_preview_job.py';exec(compile(f.read_text(),str(f),'exec'),dict(globals(),__file__=str(f)))
