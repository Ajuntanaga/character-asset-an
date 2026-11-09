"""Blend the extended wrist into the forearm; preserve mesh and finger weights."""
import bpy,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'production_v403_wrist_blend';O.mkdir(exist_ok=True)
s=bpy.context.scene;assert not bpy.app.is_job_running('RENDER')
r=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];assert len(r.animation_data.drivers)==1957
o=bpy.data.objects['V357_ANATOMICAL_HAND.R'];h=o.vertex_groups['DEF-Hand.R'];f=o.vertex_groups['DEF-Forearm_2.R'];backup=[]
for v in o.data.vertices:
 weights={w.group:w.weight for w in v.groups}
 total=weights.get(h.index,0)+weights.get(f.index,0)
 if total<.999 or v.co.z<=.005:continue
 t=max(0,min(1,(v.co.z-.005)/.070));t=t*t*(3-2*t)
 backup.append({'vertex':v.index,'weights':[(o.vertex_groups[k].name,w) for k,w in weights.items()]})
 h.add([v.index],1-t,'REPLACE');f.add([v.index],t,'REPLACE')
o.data.update();bpy.context.view_layer.update()
(O/'weights_before.json').write_text(json.dumps(backup,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(O/'Character_An_wrist_blend_v403.blend'),compress=True)
q=json.loads((R/'pipeline/render_preview_request.json').read_text());q['output']='production_v403_wrist_blend/v403_pick_close.png';(R/'pipeline/render_preview_request.json').write_text(json.dumps(q))
exec(compile((R/'pipeline/render_preview_job.py').read_text(),str(R/'pipeline/render_preview_job.py'),'exec'))
print(json.dumps({'changed_vertices':len(backup),'drivers':len(r.animation_data.drivers)}))
