"""Bounded joint palm/finger fit with inter-finger separation penalties."""
import bpy,json,sys,numpy as np
from pathlib import Path
from mathutils import Vector,Euler
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
from pipeline.guitar_geometry import GuitarGeometry,load_authoritative_mapping
out=root/'production_v479_fretting_palm';out.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
r=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];g=bpy.data.objects['V206_GUITAR_ROOT'];inv=g.matrix_world.inverted();geo=GuitarGeometry.from_mapping(load_authoritative_mapping())
digits=['Index','Middle','Ring','Pinky'];ctrl=r.pose.bones['IK-Hand.L'];base=ctrl.matrix.copy()
bs=[r.pose.bones[f'FK-Finger_{d}{j}.L'] for d in digits for j in [1,2,3]]
bak=out/'original_pose.json';assert not bak.exists()
bak.write_text(json.dumps({b.name:[list(row) for row in b.matrix_basis] for b in [ctrl]+bs}))
target=[]
for string,fret,h in [('S6',11,0),('S6',10,.010),('S7',9,0),('S8',11,0)]:
 p=geo.local_pad_from_neutral(string,fret);target.append([.260+p[0],p[1],.02645+h])
target=np.array(target)
params=[]
for d in digits:
 for j in [1,2,3]:params.append((r.pose.bones[f'FK-Finger_{d}{j}.L'],0))
 params.append((r.pose.bones[f'FK-Finger_{d}1.L'],2))
x=np.array([0.]*6+[b.rotation_euler[a] for b,a in params]);x0=x.copy()
lo=np.array([-.045]*3+[-.65]*3+[-.10,0,0,-.45]*4)
hi=np.array([.045]*3+[.65]*3+[1.9,2.,1.7,.45]*4);x=np.clip(x,lo,hi)
# Sample bone capsules; 9mm centreline separation is a conservative first fit,
# not an evaluated mesh collision certificate.
fractions=np.linspace(0,1,6)[:,None]
def apply(q):
 m=base.copy();rot=Euler(tuple(q[3:6]),'XYZ').to_matrix().to_4x4();m=rot@m
 m.translation=base.translation+r.matrix_world.inverted().to_3x3()@g.matrix_world.to_3x3()@Vector(q[:3]);ctrl.matrix=m
 for (b,a),v in zip(params,q[6:]):b.rotation_euler[a]=float(v)
 r.update_tag();bpy.context.view_layer.update()
 points=[];tails=[]
 for d in digits:
  samples=[]
  for j in [1,2,3]:
   b=r.pose.bones[f'DEF-Finger_{d}{j}.L'];a=np.array(inv@r.matrix_world@b.head);z=np.array(inv@r.matrix_world@b.tail)
   samples.extend(a+(z-a)*fractions)
  points.append(np.array(samples));tails.append(z)
 separation=[]
 for a in range(4):
  for b in range(a+1,4):separation.append(float(np.linalg.norm(points[a][:,None]-points[b][None,:],axis=2).min()))
 tails=np.array(tails)
 residual=np.concatenate([(tails-target).ravel(),3*np.maximum(0,.009-np.array(separation)),.003*(q[3:6]),.0015*(q[6:]-x0[6:])])
 return residual,tails,separation
initial=apply(x);best=float(initial[0]@initial[0]);bestx=x.copy()
for iteration in range(24):
 res,_,_=apply(x);jac=np.zeros((len(res),len(x)))
 for k in range(len(x)):
  q=x.copy();eps=.00015 if k<3 else .003;q[k]+=eps;jac[:,k]=(apply(q)[0]-res)/eps
 step=np.linalg.solve(jac.T@jac+np.diag([.02]*3+[.00002]*(len(x)-3)),-jac.T@res)
 step=np.clip(step,[-.008]*3+[-.12]*(len(x)-3),[.008]*3+[.12]*(len(x)-3))
 candidates=[]
 for gain in [1,.35,.1]:
  q=np.clip(x+gain*step,lo,hi);v=apply(q)[0];candidates.append((float(v@v),q))
 score,x=min(candidates,key=lambda item:item[0])
 if score<best:best=score;bestx=x.copy()
 if iteration%6==0:(out/'progress.json').write_text(json.dumps({'iteration':iteration,'score':best}))
res,tails,sep=apply(bestx)
report={'initial_error_mm':list(np.linalg.norm(initial[1]-target,axis=1)*1000),'final_error_mm':list(np.linalg.norm(tails-target,axis=1)*1000),'sampled_separation_mm':list(np.array(sep)*1000),'params':list(bestx),'drivers':len(r.animation_data.drivers)}
(out/'trial.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
(root/'pipeline/render_preview_request.json').write_text(json.dumps({'output':'production_v479_fretting_palm/trial.png','resolution':[900,700],'samples':24,'scale':.30,'camera':list(g.matrix_world@Vector((.35,.28,.38))),'target':list(g.matrix_world@Vector((.35,.01,.035)))}))
f=root/'pipeline/render_preview_job.py';exec(compile(f.read_text(),str(f),'exec'),dict(globals(),__file__=str(f)))
