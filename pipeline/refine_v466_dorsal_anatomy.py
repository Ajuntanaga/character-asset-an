"""Shape dorsal hand landmarks while preserving the pinch, rig and topology."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1];out=root/'production_v466_dorsal_anatomy';out.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
assert 'v460' in bpy.data.filepath
backup=out/'original_coordinates.json';assert not backup.exists()
source=json.loads((root/'production_v359_hand_weights/rest_hand_data.json').read_text())['bones']
original={};report={}
for side in ('R','L'):
 o=bpy.data.objects['V357_ANATOMICAL_HAND.'+side]
 original[side]=[list(v.co) for v in o.data.vertices]
backup.write_text(json.dumps(original))
for side in ('R','L'):
 o=bpy.data.objects['V357_ANATOMICAL_HAND.'+side]
 nail_vertices={i for p in o.data.polygons if p.material_index==1 for i in p.vertices}
 changed=[]
 for v in o.data.vertices:
  weights={o.vertex_groups[w.group].name:w.weight for w in v.groups}
  if v.index in nail_vertices or any(w>.001 and ('Thumb' in n or 'Index' in n) for n,w in weights.items()):continue
  x,y,z=v.co
  if y>=0 or v.normal.y>=-.25:continue
  dorsal=min(1.,max(0.,(-v.normal.y-.25)/.55))*min(1.,-y/.009)
  displacement=0.
  for digit in ('Middle','Ring','Pinky'):
   mcp=Vector(source[f'DEF-Finger_{digit}1.L']['head'])
   pip=Vector(source[f'DEF-Finger_{digit}1.L']['tail'])
   start_z=-.025
   t=(z-start_z)/(mcp.z-start_z)
   if 0<t<1:
    center_x=mcp.x*(.45+.55*t)
    displacement+=.0022*math.exp(-.5*((x-center_x)/.0038)**2)*math.sin(math.pi*t)**.65
   displacement+=.0012*math.exp(-.5*(((x-mcp.x)/.007)**2+((z-mcp.z)/.008)**2))
   displacement+=.0009*math.exp(-.5*(((x-pip.x)/.005)**2+((z-pip.z)/.006)**2))
  displacement*=dorsal
  if displacement>1e-6:v.co.y-=displacement;changed.append((v.index,displacement))
 o.data.update();o.update_tag()
 report[side]={'changed_vertices':len(changed),'max_local_displacement':max((d for _,d in changed),default=0),'nail_vertices_preserved':len(nail_vertices)}
bpy.context.view_layer.update()
report['drivers']=len(bpy.data.objects['V357_CLOUDRIG_CONTROLS'].animation_data.drivers);assert report['drivers']==1957
(out/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
g=bpy.data.objects['V206_GUITAR_ROOT']
(root/'pipeline/render_preview_request.json').write_text(json.dumps({'output':'production_v466_dorsal_anatomy/playing.png','resolution':[720,640],'samples':24,'scale':.23,'camera':list(g.matrix_world@Vector((.68,.28,.42))),'target':list(g.matrix_world@Vector((.635,-.02,.045)))}))
f=root/'pipeline/render_preview_job.py';exec(compile(f.read_text(),str(f),'exec'),dict(globals(),__file__=str(f)))
