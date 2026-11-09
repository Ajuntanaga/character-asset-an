"""Reversible palm-width trial with protected grip and unchanged finger joints."""
import bpy,json,math
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'production_v467_palm_silhouette';out.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
assert 'v466' in bpy.data.filepath
h=bpy.data.objects['V357_ANATOMICAL_HAND.R']
backup=out/'coordinates.json';assert not backup.exists()
backup.write_text(json.dumps([list(v.co) for v in h.data.vertices]))
changes=[]
for v in h.data.vertices:
 weights={h.vertex_groups[w.group].name:w.weight for w in v.groups}
 if any(w>.001 and ('Thumb' in n or 'Index' in n) for n,w in weights.items()):continue
 x,y,z=v.co
 # Expand ulnar palm only, taper to unchanged wrist and MCP joints.
 t=(-z-.025)/.085
 if not 0<t<1 or x>.02:continue
 delta=-.007*math.sin(math.pi*t)**1.2*min(1.,max(0.,(.02-x)/.055))
 v.co.x+=delta;changes.append(abs(delta))
h.data.update();h.update_tag();bpy.context.view_layer.update()
r={'vertices_changed':len(changes),'max_displacement_m':max(changes),'drivers':len(bpy.data.objects['V357_CLOUDRIG_CONTROLS'].animation_data.drivers),'status':'unsaved silhouette trial; grip and finger joints retained'}
assert r['drivers']==1957
(out/'report.json').write_text(json.dumps(r,indent=2));print(json.dumps(r))
(root/'pipeline/render_preview_request.json').write_text(json.dumps({'output':'production_v467_palm_silhouette/full.png','resolution':[720,960],'samples':24,'scale':2.12,'camera':[.35,-3.5,1.3],'target':[0,0,.94]}))
f=root/'pipeline/render_preview_job.py';exec(compile(f.read_text(),str(f),'exec'),dict(globals(),__file__=str(f)))
