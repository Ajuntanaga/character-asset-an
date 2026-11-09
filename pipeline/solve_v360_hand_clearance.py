"""Fit fretting controls with phalanx separation and a thumb behind the neck.

This is an initial geometric fit. Blender's evaluated skin and rendered views
remain the acceptance check; centerline clearance alone is insufficient.
"""
import json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

ROOT=Path('/home/ajuntanaga/Projects/Blender/Character Asset_An')
OUT=ROOT/'production_v360_hand_clearance';OUT.mkdir(exist_ok=True)
src=json.loads((ROOT/'production_v359_hand_weights/rest_control_transforms.json').read_text())
old=json.loads((ROOT/'production_v358_hand_contact/fretting_solution.json').read_text())
B=src['bones'];base=np.array(old['hand_matrix_guitar'])
rest_inv=np.linalg.inv(B['IK-Hand.L']['rest'])
digits=['Index','Middle','Ring','Pinky'];chains={}
for d in digits+['Thumb']:
 names=[f'FK-Finger_{d}{i}.L' for i in (1,2,3)]
 rest=[np.array(B[n]['rest']) for n in names]
 chains[d]=[rest_inv@rest[0],np.linalg.inv(rest[0])@rest[1],np.linalg.inv(rest[1])@rest[2]]

def rot(v):
 m=np.eye(4);m[:3,:3]=Rotation.from_euler('xyz',v).as_matrix();return m

def chain(hand,d,a):
 m=hand@chains[d][0]@rot([a[0],a[4],a[3]]);pts=[m[:3,3].copy()]
 for i in (1,2):
  m=m@chains[d][i]@rot([a[i],0,0]);pts.append(m[:3,3].copy())
 pts.append((m@np.array([0,B[f'FK-Finger_{d}3.L']['length'],0,1]))[:3])
 return np.array(pts),m

targets={d:np.array(old['fingers'][d]['target']) for d in digits}
# Adjacent D/G strings need staggered contact within the same ninth fret cell.
targets['Ring'][0]-=.006
targets['Pinky'][0]+=.0005
targets['Index'][2]=.027
targets['Middle'][2]=.027
targets['Ring'][2]=.027
targets['Pinky'][2]=.026
x0=np.r_[np.zeros(6),np.concatenate([np.radians(old['fingers'][d]['angles_degrees']) for d in digits])]
lo=np.r_[np.radians([-20,-20,-20]),[-.020,-.020,-.005],np.tile(np.radians([-20,0,0,-45,-20]),4)]
hi=np.r_[np.radians([20,20,20]),[.020,.020,.020],np.tile(np.radians([95,115,90,45,20]),4)]

def hand_matrix(x):
 m=base.copy();m[:3,:3]=Rotation.from_rotvec(x[:3]).as_matrix()@base[:3,:3];m[:3,3]+=x[3:6];return m

def samples(pts,d):
 # Ignore shared webbing at the MCP; retain the entire mobile finger.
 t=np.array([.25,.50,.75,1.])
 q=np.concatenate([pts[i][None,:]+t[:,None]*(pts[i+1]-pts[i])[None,:] for i in range(3)])
 radii=np.interp(np.r_[t,1+t,2+t],[0,1,2,3],[.0078,.0070,.0055,.0035])
 if d=='Pinky':radii*=.84
 return q,radii

def residual(x):
 hand=hand_matrix(x);r=list(x[:3]*.002)+list(x[3:6]*.18);sampled={}
 for i,d in enumerate(digits):
  a=x[6+5*i:11+5*i];p,m=chain(hand,d,a);sampled[d]=samples(p,d)
  r.extend((p[-1]-targets[d])*15)
  r.extend(np.maximum(0,np.array([.038,.052,.039])-p[:3,2])*2)
  r.append(max(0,m[2,1]/np.linalg.norm(m[:3,1])+.50)*.02)
  r.append((a[2]-.60*a[1])*.0015)
  r.extend(a[3:]*.0007)
  r.extend((a[:3]-np.radians([25,65,35]))*.0004)
 for i,d in enumerate(digits):
  p,pr=sampled[d]
  for e in digits[i+1:]:
   q,qr=sampled[e];dist=np.linalg.norm(p[:,None,:]-q[None,:,:],axis=2)
   r.extend((np.maximum(0,pr[:,None]+qr[None,:]+.0007-dist)*5).ravel())
 return np.array(r)

sol=least_squares(residual,x0,bounds=(lo,hi),max_nfev=200,ftol=1e-9,xtol=1e-9,gtol=1e-9)
hand=hand_matrix(sol.x)
report={'source':'V359','voicing':old['voicing'],'hand_matrix_guitar':hand.tolist(),'solver_cost':sol.cost,'evaluations':sol.nfev,'fingers':{}}
for i,d in enumerate(digits):
 a=sol.x[6+5*i:11+5*i];p,m=chain(hand,d,a)
 report['fingers'][d]={'angles_degrees':np.degrees(a).tolist(),'target':targets[d].tolist(),'points':p.tolist(),'tip_error_mm':float(np.linalg.norm(p[-1]-targets[d])*1000)}

# Keep the thumb centerline far enough behind the neck for its actual skin.
target=np.array([.285,.002,-.041])
def thumb_res(a):
 p,m=chain(hand,'Thumb',a)
 return np.r_[(p[-1]-target)*12,np.maximum(0,p[1:,2]+.038)*8,(a-np.radians(old['fingers']['Thumb']['angles_degrees']))*.001]
tl=np.radians([-65,-40,-30,-85,-85]);th=np.radians([90,90,90,85,85])
ts=least_squares(thumb_res,np.radians(old['fingers']['Thumb']['angles_degrees']),bounds=(tl,th),max_nfev=200)
p,m=chain(hand,'Thumb',ts.x)
report['fingers']['Thumb']={'angles_degrees':np.degrees(ts.x).tolist(),'target':target.tolist(),'points':p.tolist(),'tip_error_mm':float(np.linalg.norm(p[-1]-target)*1000)}
(OUT/'fretting_solution.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
