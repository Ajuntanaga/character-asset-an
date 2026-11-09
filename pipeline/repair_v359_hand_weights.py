"""Replace cross-digit heat-weight leakage with localized phalanx weights.

Preserves the CC0 hand mesh, multires detail, native CloudRig and original files.
The known rest centerlines classify each finger. Weights blend around the real
MCP/PIP/DIP centers rather than propagating between adjacent fingers.
"""
import bpy,json,math
import numpy as np
from pathlib import Path
ROOT=Path('/home/ajuntanaga/Projects/Blender/Character Asset_An')
OUT=ROOT/'production_v359_hand_weights';OUT.mkdir(exist_ok=True)
scene=bpy.context.scene
rig=next(o for o in scene.objects if o.name.endswith('_CLOUDRIG_CONTROLS'))
source=json.loads((OUT/'rest_hand_data.json').read_text())
points={}
for d in ('Index','Middle','Ring','Pinky','Thumb'):
 bones=[source['bones'][f'DEF-Finger_{d}{i}.L'] for i in (1,2,3)]
 points[d]=np.array([bones[0]['head'],bones[0]['tail'],bones[1]['tail'],bones[2]['tail']])

def smooth(x):
 x=np.clip(x,0.,1.);return x*x*(3-2*x)

def project(p,pts):
 a=pts[:-1];delta=np.diff(pts,axis=0);length=np.linalg.norm(delta,axis=1)
 t=np.einsum('ij,ij->i',p-a,delta)/(length*length)
 near=a+np.clip(t,0,1)[:,None]*delta
 dist=np.linalg.norm(p-near,axis=1);k=int(np.argmin(dist))
 # Preserve negative longitudinal distance at the MCP for the palm transition.
 s=np.r_[0,np.cumsum(length)][k]+(t[k] if k==0 else np.clip(t[k],0,1))*length[k]
 return dist[k],s,length

report={'method':'nearest rest phalanx chain; smooth joint blends; no cross-digit distal weights','hands':{}}
for side in ('L','R'):
 o=next(o for o in scene.objects if o.name.endswith('_ANATOMICAL_HAND.'+side))
 backup=OUT/f'original_weights_{side}.json'
 if not backup.exists():
  backup.write_text(json.dumps([{o.vertex_groups[w.group].name:w.weight for w in v.groups} for v in o.data.vertices]))
 counts={d:0 for d in points};total_error=0.;digit_ids={d:[] for d in points}
 for v in o.data.vertices:
  p=np.array(v.co);candidates={d:project(p,pts) for d,pts in points.items()}
  digit=min(candidates,key=lambda d:candidates[d][0]);distance,s,length=candidates[digit]
  # The thumb has a long thenar transition; fingers blend around their MCP.
  start,end=(-.020,.018) if digit=='Thumb' else (-.012,.012)
  influence=float(smooth((s-start)/(end-start)))
  # Distant palm vertices should follow the hand, even near the thumb root.
  if digit=='Thumb':influence*=float(1-smooth((distance-.020)/.015))
  w={f'DEF-Hand.{side}':1-influence}
  j1,j2=length[0],length[0]+length[1]
  width=.0065 if digit!='Thumb' else .007
  t1=float(smooth((s-j1+width)/(2*width)));t2=float(smooth((s-j2+width)/(2*width)))
  w[f'DEF-Finger_{digit}1.{side}']=influence*(1-t1)
  w[f'DEF-Finger_{digit}2.{side}']=influence*t1*(1-t2)
  w[f'DEF-Finger_{digit}3.{side}']=influence*t2
  total=sum(w.values());w={n:x/total for n,x in w.items() if x>1e-7}
  for old in list(v.groups):o.vertex_groups[old.group].remove([v.index])
  for name,value in w.items():
   group=o.vertex_groups.get(name) or o.vertex_groups.new(name=name);group.add([v.index],value,'REPLACE')
  if influence>.8:counts[digit]+=1;digit_ids[digit].append(v.index)
  total_error=max(total_error,abs(sum(w.values())-1))
 o.data.update();o.update_tag()
 report['hands'][side]={'vertices':len(o.data.vertices),'max_weight_sum_error':total_error,'finger_counts':counts,'finger_vertices':digit_ids}
 o['weight_method_v359']=report['method']
bpy.context.view_layer.update()
(OUT/'weight_repair_report.json').write_text(json.dumps(report,indent=2))
print(json.dumps({s:{k:v for k,v in x.items() if k!='finger_vertices'} for s,x in report['hands'].items()}))
