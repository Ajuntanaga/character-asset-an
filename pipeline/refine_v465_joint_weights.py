"""Narrow free-finger MCP transitions without altering the picking pinch."""
import bpy,json
import numpy as np
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'production_v465_joint_weights';out.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
o=bpy.data.objects['V357_ANATOMICAL_HAND.R']
backup=out/'original_weights.json'
assert not backup.exists(), 'Trial already applied; restore before rerunning'
original=[{o.vertex_groups[w.group].name:w.weight for w in v.groups} for v in o.data.vertices]
backup.write_text(json.dumps(original))
source=json.loads((root/'production_v359_hand_weights/rest_hand_data.json').read_text())
changed=[]
for digit in ('Middle','Ring','Pinky'):
 b=source['bones'][f'DEF-Finger_{digit}1.L'];a=np.array(b['head']);delta=np.array(b['tail'])-a;axis=delta/np.linalg.norm(delta)
 names=[f'DEF-Finger_{digit}{i}.R' for i in (1,2,3)]
 for v,w in zip(o.data.vertices,original):
  influence=sum(w.get(n,0) for n in names)
  if not 0<influence<.9999 or w.get('DEF-Hand.R',0)<=0:continue
  s=float(np.dot(np.array(v.co)-a,axis))
  # Concentrate the bend over 12mm around MCP instead of 24mm.
  t=max(0.,min(1.,(s+.006)/.012));new=t*t*(3-2*t)
  for name in names:
   o.vertex_groups[name].add([v.index],new*w.get(name,0)/influence,'REPLACE')
  o.vertex_groups['DEF-Hand.R'].add([v.index],1-new,'REPLACE')
  changed.append(v.index)
o.data.update();o.update_tag();bpy.context.view_layer.update()
(out/'report.json').write_text(json.dumps({'changed_vertices':changed,'preserved':'thumb and index weights, geometry and rig controls'}))
(out/'mode.txt').write_text('curl')
p=root/'pipeline/check_v462_hand_deformation.py';s=p.read_text().replace('production_v462_hand_deformation','production_v465_joint_weights')
exec(compile(s,str(p),'exec'),dict(globals(),__file__=str(p)))
