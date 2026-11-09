"""Local cross-digit web diffusion trial, with exact weight backup."""
import bpy,json
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'production_v489_web_weights';out.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
o=bpy.data.objects['V357_ANATOMICAL_HAND.R']
weights=[{o.vertex_groups[g.group].name:g.weight for g in v.groups} for v in o.data.vertices]
p=out/'original_weights.json'
assert not p.exists(),'Do not compound trial'
p.write_text(json.dumps(weights))
adj=[set() for v in weights]
for e in o.data.edges:
 a,b=e.vertices;adj[a].add(b);adj[b].add(a)
def digit(w):
 items=[(v,k) for k,v in w.items() if 'Finger_' in k]
 return max(items)[1].split('Finger_')[1][:-3] if items else ''
digits=[digit(w) for w in weights];allowed={'Middle','Ring','Pinky'}
seeds=set()
for e in o.data.edges:
 a,b=e.vertices
 if digits[a] in allowed and digits[b] in allowed and digits[a]!=digits[b]:seeds.update((a,b))
region=seeds|{j for i in seeds for j in adj[i] if digits[j] in allowed}
nails={v for f in o.data.polygons if f.material_index==1 for v in f.vertices};region-=nails
current=weights
for _ in range(3):
 nxt=[dict(w) for w in current]
 for i in region:
  neighbors=[j for j in adj[i] if digits[j] in allowed]
  if not neighbors:continue
  alpha=.45 if i in seeds else .15
  keys=set(current[i])|{k for j in neighbors for k in current[j]}
  nxt[i]={k:(1-alpha)*current[i].get(k,0)+alpha*sum(current[j].get(k,0) for j in neighbors)/len(neighbors) for k in keys}
 current=nxt
for i in region:
 for g in o.vertex_groups:g.remove([i])
 for name,w in current[i].items():
  if w>1e-8:o.vertex_groups[name].add([i],w,'REPLACE')
o.data.update();bpy.context.view_layer.update()
(out/'trial.json').write_text(json.dumps({'seed_count':len(seeds),'changed_count':len(region),'indices':sorted(region),'drivers':len(bpy.data.objects['V357_CLOUDRIG_CONTROLS'].animation_data.drivers)},indent=2))
f=root/'pipeline/trial_v488_relaxed_knuckles.py'
s=f.read_text().replace("'production_v488_reference_pick_curl'","'production_v488_reference_pick_curl'").replace('production_v488_reference_pick_curl/relaxed_check.json','production_v489_web_weights/check.json').replace('production_v488_reference_pick_curl/relaxed.png','production_v489_web_weights/trial.png')
exec(compile(s,str(f),'exec'),dict(globals(),__file__=str(f)))
