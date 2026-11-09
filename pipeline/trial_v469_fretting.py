import bpy,json,sys,math,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
from pipeline.guitar_geometry import GuitarGeometry,load_authoritative_mapping
out=root/'production_v469_fretting';assert not bpy.app.is_job_running('RENDER')
r=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];g=bpy.data.objects['V206_GUITAR_ROOT'];geo=GuitarGeometry.from_mapping(load_authoritative_mapping())
bones=[r.pose.bones[f'FK-Finger_{d}{j}.L'] for d in ('Index','Middle','Ring','Pinky') for j in (1,2,3)]
bak=out/'original_pose.json';assert not bak.exists();bak.write_text(json.dumps({b.name:[list(row) for row in b.matrix_basis] for b in bones},indent=2))
report=[]
for digit,string,fret,hover in [('Index','S6',11,0),('Middle','S6',10,.010),('Ring','S7',9,0),('Pinky','S8',11,0)]:
 p=geo.local_pad_from_neutral(string,fret);target=g.matrix_world@Vector((.260+p[0],p[1],.02645+hover));t=np.array(target)
 bs=[r.pose.bones[f'FK-Finger_{digit}{j}.L'] for j in (1,2,3)];params=[(bs[0],0),(bs[0],1),(bs[0],2),(bs[1],0),(bs[2],0)]
 lo=np.array([-.15,-.75,-.75,0,0]);hi=np.array([1.8,.75,.75,2,1.6]);x=np.clip(np.array([b.rotation_euler[a] for b,a in params]),lo,hi)
 def apply(q):
  for (b,a),v in zip(params,q):b.rotation_euler[a]=float(v)
  r.update_tag();bpy.context.view_layer.update()
  return np.array(r.matrix_world@r.pose.bones[f'DEF-Finger_{digit}3.L'].tail)
 best=x.copy();besterr=float(np.linalg.norm(t-apply(x)));initial=besterr
 for it in range(45):
  pos=apply(x);err=t-pos
  if np.linalg.norm(err)<.0004:break
  jac=np.zeros((3,5));eps=.003
  for j in range(5):
   q=x.copy();q[j]+=eps;jac[:,j]=(apply(q)-pos)/eps
  step=jac.T@np.linalg.solve(jac@jac.T+np.eye(3)*.000002,err);step=np.clip(step,-.15,.15)
  choices=[]
  for gain in (1,.3,.08):
   q=np.clip(x+gain*step,lo,hi);choices.append((float(np.linalg.norm(t-apply(q))),q.copy()))
  v,x=min(choices,key=lambda z:z[0])
  if v<besterr:besterr=v;best=x.copy()
 apply(best);report.append(dict(digit=digit,initial_mm=initial*1000,final_mm=besterr*1000,angles=list(np.degrees(best))))
assert len(r.animation_data.drivers)==1957
(out/'trial.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
req={'output':'production_v469_fretting/trial.png','resolution':[900,700],'samples':24,'scale':.30,'camera':list(g.matrix_world@Vector((.35,.28,.38))),'target':list(g.matrix_world@Vector((.35,.01,.035)))}
(root/'pipeline/render_preview_request.json').write_text(json.dumps(req));f=root/'pipeline/render_preview_job.py';exec(compile(f.read_text(),str(f),'exec'),dict(globals(),__file__=str(f)))
