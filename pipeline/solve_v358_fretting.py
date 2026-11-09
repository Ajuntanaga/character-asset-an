"""Fit the CloudRig FK chains to an E-minor voicing in guitar coordinates.
This operates on exported control transforms; the result must be checked on
Blender's evaluated hand surfaces before it is accepted.
"""
import json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

ROOT=Path('/home/ajuntanaga/Projects/Blender/Character Asset_An')
OUT=ROOT/'production_v358_hand_contact';OUT.mkdir(exist_ok=True)
source=json.loads(Path('/tmp/bca_v358_all_bones.json').read_text())
B=source['bones'];G=np.array(source['guitar']);Gi=np.linalg.inv(G)
base=Gi@np.array(B['IK-Hand.L']['matrix'])
rest_inv=np.linalg.inv(B['IK-Hand.L']['rest'])
digits=['Index','Middle','Ring','Pinky']
chains={}
for digit in digits+['Thumb']:
 names=[f'FK-Finger_{digit}{i}.L' for i in range(1,4)]
 rest=[np.array(B[n]['rest']) for n in names]
 chains[digit]=[rest_inv@rest[0],np.linalg.inv(rest[0])@rest[1],np.linalg.inv(rest[1])@rest[2]]

def rot(v):
 m=np.eye(4);m[:3,:3]=Rotation.from_euler('xyz',v).as_matrix();return m

def chain(hand,digit,angles):
 # MCP flexion, PIP flexion, DIP flexion, MCP abduction, axial rotation.
 flex1,flex2,flex3,spread,twist=angles
 m=hand@chains[digit][0]@rot([flex1,twist,spread]);points=[m[:3,3].copy()]
 for i,flex in ((1,flex2),(2,flex3)):
  m=m@chains[digit][i]@rot([flex,0,0]);points.append(m[:3,3].copy())
 tip=(m@np.array([0,B[f'FK-Finger_{digit}3.L']['length'],0,1]))[:3]
 return np.array(points+[tip]),m

def fret_target(string,fret):
 # Eight strings, 28 to 26.5 inch scales, neutral fret 7.
 t=(string-1)/7;length=(28-1.5*t)*.0254
 nx=.260-length*(1-2**(-7/12));ny=-.0245+.049*t
 f=1-2**(-fret/12);x=nx+length*f-.004
 y=ny*(1+.5*((x-nx)/length))
 return np.array([x,y,.0265])

targets=dict(zip(digits,[fret_target(4,7),fret_target(7,8),fret_target(5,9),fret_target(6,9)]))
x0=np.r_[np.zeros(3),[-.014,-.008,.024],np.tile(np.radians([30,45,30,0,0]),4)]
lo=np.r_[np.radians([-25,-25,-25]),[-.040,-.040,.005],np.tile(np.radians([-15,0,0,-35,-12]),4)]
hi=np.r_[np.radians([25,25,25]),[.020,.030,.055],np.tile(np.radians([95,115,85,35,12]),4)]

def hand_matrix(v):
 m=base.copy();m[:3,:3]=Rotation.from_rotvec(v[:3]).as_matrix()@base[:3,:3];m[:3,3]=base[:3,3]+v[3:6];return m

def residual(v):
 hand=hand_matrix(v);r=[]
 r.extend(v[:3]*.006);r.extend((v[3:6]-x0[3:6])*.35)
 for i,d in enumerate(digits):
  a=v[6+5*i:11+5*i];p,m=chain(hand,d,a)
  r.extend((p[-1]-targets[d])*12)
  # Arch the PIP and DIP above the fretboard, avoid side-wall contact at MCP.
  r.extend(np.maximum(0,np.array([.038,.052,.040])-p[:3,2])*2)
  direction=m[:3,1]/np.linalg.norm(m[:3,1])
  r.append(max(0,direction[2]+.50)*.015)
  r.append((a[2]-.60*a[1])*.002)
  r.extend(a[3:]*.002)
  r.extend((a[:3]-np.radians([30,55,30]))*.0005)
 return np.array(r)

sol=least_squares(residual,x0,bounds=(lo,hi),max_nfev=350,ftol=1e-10,xtol=1e-10,gtol=1e-10)
hand=hand_matrix(sol.x)
report={'source':'V357','voicing':'E minor: A7 D9 G9 B8, high E open; low strings inactive',
        'hand_matrix_guitar':hand.tolist(),'wrist_delta_m':sol.x[3:6].tolist(),'rotation_delta_degrees':np.degrees(sol.x[:3]).tolist(),'fingers':{},'solver_cost':sol.cost,'evaluations':sol.nfev}
for i,d in enumerate(digits):
 a=sol.x[6+5*i:11+5*i];p,m=chain(hand,d,a)
 report['fingers'][d]={'angles_degrees':np.degrees(a).tolist(),'target':targets[d].tolist(),'points':p.tolist(),'tip_error_mm':float(np.linalg.norm(p[-1]-targets[d])*1000)}
# Thumb opposes the middle finger on the back of the neck; keep the full chain behind it.
target=np.array([.285,.002,-.034])
def thumb_res(a):
 p,m=chain(hand,'Thumb',a)
 return np.r_[(p[-1]-target)*12,np.maximum(0,p[1:,2]+.033)*5,(a-np.radians([20,15,10,0,0]))*.001]
t0=np.radians([20,15,10,0,0]);tl=np.radians([-65,-30,-20,-80,-80]);th=np.radians([90,90,90,80,80])
ts=least_squares(thumb_res,t0,bounds=(tl,th),max_nfev=300)
p,m=chain(hand,'Thumb',ts.x)
report['fingers']['Thumb']={'angles_degrees':np.degrees(ts.x).tolist(),'target':target.tolist(),'points':p.tolist(),'tip_error_mm':float(np.linalg.norm(p[-1]-target)*1000)}
(OUT/'fretting_solution.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
