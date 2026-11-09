"""Fit existing FK controls to reference chord targets; candidate requires mesh review."""
import bpy,json,sys,math,numpy as np
from pathlib import Path
from mathutils import Vector, Matrix
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
from pipeline.guitar_geometry import GuitarGeometry,load_authoritative_mapping
out=root/'production_v433_palm_orientation';out.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
bpy.ops.wm.open_mainfile(filepath=str(root/'production_v430_fret_clearance/Character_An_fret_clearance_v430.blend'))
rig=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];g=bpy.data.objects['V206_GUITAR_ROOT'];geo=GuitarGeometry.from_mapping(load_authoritative_mapping())
normal=(g.matrix_world.to_3x3()@Vector((0,0,1))).normalized()
ctrl=rig.pose.bones['IK-Hand.L'];before={'wrist':[list(v) for v in ctrl.matrix_basis],'fingers':{}}
for d in ('Index','Middle','Ring','Pinky'):
 before['fingers'][d]=[list(rig.pose.bones[f'FK-Finger_{d}{j}.L'].rotation_euler) for j in (1,2,3)]
(out/'before.json').write_text(json.dumps(before,indent=2))
# Rotate about the knuckle centroid, preserving the palm's location.
center=sum((rig.matrix_world@rig.pose.bones[f'DEF-Finger_{d}1.L'].head for d in ('Index','Middle','Ring','Pinky')),Vector())/4
rotation=Matrix.Rotation(math.radians(55),4,'Y')
world=rig.matrix_world@ctrl.matrix
ctrl.matrix=rig.matrix_world.inverted()@Matrix.Translation(center)@rotation@Matrix.Translation(-center)@world
for d in ('Index','Middle','Ring','Pinky'):
 for j,angle in ((1,25),(2,45),(3,20)):
  rig.pose.bones[f'FK-Finger_{d}{j}.L'].rotation_euler=(math.radians(angle),0,0)
rig.update_tag();bpy.context.view_layer.update()
report=[]
for digit,string,fret,hover in [('Index','S6',11,0),('Middle','S6',10,.010),('Ring','S7',9,0),('Pinky','S8',11,0)]:
 p=geo.local_pad_from_neutral(string,fret,behind_fraction=.18);surface=g.matrix_world@Vector((.260+p[0],p[1],.02045));target=surface+normal*(.006+hover)
 bones=[rig.pose.bones[f'FK-Finger_{digit}{j}.L'] for j in (1,2,3)]
 params=[(bones[0],0),(bones[0],1),(bones[0],2),(bones[1],0),(bones[2],0)]
 lo=np.array([-.1,-.3,-.3,0,0]);hi=np.array([1.7,.3,.3,1.6,1.3]);x=np.array([b.rotation_euler[a] for b,a in params]);x=np.clip(x,lo,hi)
 def apply(q):
  for (b,a),v in zip(params,q):b.rotation_euler[a]=float(v)
  rig.update_tag();bpy.context.view_layer.update()
  return np.array(rig.matrix_world@rig.pose.bones[f'DEF-Finger_{digit}3.L'].tail)
 t=np.array(target);initial=float(np.linalg.norm(apply(x)-t));best=x.copy();besterr=initial
 for iteration in range(18):
  pos=apply(x);error=t-pos
  if np.linalg.norm(error)<.0005:break
  jac=np.zeros((3,5));eps=.003
  for j in range(5):
   q=x.copy();q[j]+=eps;jac[:,j]=(apply(q)-pos)/eps
  step=jac.T@np.linalg.solve(jac@jac.T+np.eye(3)*.000003,error)
  step=np.clip(step,-.20,.20)
  candidate=np.clip(x+step,lo,hi);err=float(np.linalg.norm(apply(candidate)-t))
  if err<besterr:best=candidate.copy();besterr=err
  if err>np.linalg.norm(error):candidate=np.clip(x+step*.25,lo,hi)
  x=candidate
 apply(best)
 report.append({'digit':digit,'string':string,'fret':fret,'hover_m':hover,'surface':list(surface),'target':list(target),'initial_error_m':initial,'final_error_m':besterr,'angles_degrees':list(np.degrees(best))})
assert len(rig.animation_data.drivers)==1957
(out/'report.json').write_text(json.dumps({'fingers':report,'drivers':1957,'status':'Bone-target candidate; surface contact and anatomy require visual review'},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Character_An_palm_orientation_v433.blend'))
print(json.dumps(report))
