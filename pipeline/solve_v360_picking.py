"""Fit a relaxed picking grip above the strings using CloudRig FK controls."""
import json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

ROOT=Path('/home/ajuntanaga/Projects/Blender/Character Asset_An')
OUT=ROOT/'production_v360_hand_clearance';OUT.mkdir(exist_ok=True)
src=json.loads((ROOT/'production_v359_hand_weights/rest_control_transforms.json').read_text())
B=src['bones'];base=np.linalg.inv(src['guitar'])@B['IK-Hand.R']['matrix'];base[2,3]+=.045
rest_inv=np.linalg.inv(B['IK-Hand.R']['rest']);digits=['Index','Middle','Ring','Pinky','Thumb'];chains={}
for d in digits:
 rest=[np.array(B[f'FK-Finger_{d}{i}.R']['rest']) for i in (1,2,3)]
 chains[d]=[rest_inv@rest[0],np.linalg.inv(rest[0])@rest[1],np.linalg.inv(rest[1])@rest[2]]
def rot(v):
 m=np.eye(4);m[:3,:3]=Rotation.from_euler('xyz',v).as_matrix();return m
def chain(h,d,a):
 m=h@chains[d][0]@rot([a[0],a[4],a[3]]);p=[m[:3,3].copy()]
 for i in (1,2):
  m=m@chains[d][i]@rot([a[i],0,0]);p.append(m[:3,3].copy())
 p.append((m@np.array([0,B[f'FK-Finger_{d}3.R']['length'],0,1]))[:3])
 return np.array(p),m
def hand_matrix(x):
 h=base.copy();h[:3,:3]=Rotation.from_rotvec(x[:3]).as_matrix()@base[:3,:3];h[:3,3]+=x[3:6];return h
initial={'Index':[55,90,45,0,0],'Middle':[55,90,40,0,0],'Ring':[55,90,40,0,0],'Pinky':[55,90,40,0,0],'Thumb':[20,20,10,0,0]}
x0=np.r_[np.zeros(6),np.concatenate([np.radians(initial[d]) for d in digits])]
lo=np.r_[np.radians([-20,-20,-20]),[-.020,-.020,-.010],np.tile(np.radians([0,5,0,-25,-20]),4),np.radians([-65,-35,-25,-80,-80])]
hi=np.r_[np.radians([20,20,20]),[.020,.020,.025],np.tile(np.radians([90,115,80,25,20]),4),np.radians([90,90,90,80,80])]
targets={'Index':np.array([.646,-.030,.058]),'Thumb':np.array([.641,-.025,.072])}
def residual(x):
 h=hand_matrix(x);r=list(x[:3]*.002)+list(x[3:6]*.15);poses={}
 for i,d in enumerate(digits):
  a=x[6+5*i:11+5*i];p,m=chain(h,d,a);poses[d]=p
  if d in targets:r.extend((p[-1]-targets[d])*12)
  r.extend(np.maximum(0,.039-p[:,2])*6)
  r.extend((a-np.radians(initial[d]))*(.0005 if d=='Thumb' else .0015))
  if d not in ('Index','Thumb'):r.append((a[2]-.5*a[1])*.002)
 for i,d in enumerate(digits[:-1]):
  p=poses[d][1:]
  for e in digits[i+1:-1]:
   q=poses[e][1:];dist=np.linalg.norm(p[:,None,:]-q[None,:,:],axis=2)
   r.extend((np.maximum(0,.012-dist)*3).ravel())
 # The thumb pad opposes the index; the remaining thumb must clear the curled hand.
 for d in digits[:-1]:
  p=poses[d][:-1];q=poses['Thumb'][:-1]
  r.extend((np.maximum(0,.014-np.linalg.norm(p[:,None,:]-q[None,:,:],axis=2))*3).ravel())
 return np.array(r)
sol=least_squares(residual,x0,bounds=(lo,hi),max_nfev=200,ftol=1e-9,xtol=1e-9,gtol=1e-9)
h=hand_matrix(sol.x);report={'hand_matrix_guitar':h.tolist(),'solver_cost':sol.cost,'evaluations':sol.nfev,'fingers':{}}
for i,d in enumerate(digits):
 a=sol.x[6+5*i:11+5*i];p,m=chain(h,d,a)
 report['fingers'][d]={'angles_degrees':np.degrees(a).tolist(),'points':p.tolist()}
(OUT/'picking_solution.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
