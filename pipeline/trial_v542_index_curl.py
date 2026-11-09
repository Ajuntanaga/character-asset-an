"""Redistribute index flexion with a bounded surface-contact target."""
import bpy,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1];out=root/'production_v542_index_curl';out.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(root/'production_v541_pick_exposure/Character_An_pick_exposure_TRIAL_v541.blend'))
s=bpy.context.scene;main=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];hand=bpy.data.objects['V528_NATIVE_HAND.R'];pick=bpy.data.objects['V361_NYLON_PICK'];bones=[main.pose.bones[f'FK-Finger_Index{j}.R'] for j in (1,2,3)]
sub=[(m,m.show_viewport) for m in hand.modifiers if m.type=='SUBSURF'];old=np.array([b.rotation_euler.x for b in bones]);ids=[3032,2314,3052,1836,579,580,1730,1752]
for m,_ in sub:m.show_viewport=False
bpy.context.view_layer.update()
def point():
 e=hand.evaluated_get(bpy.context.evaluated_depsgraph_get());return np.mean([list(e.matrix_world@e.data.vertices[i].co) for i in ids],axis=0)
target=point();prior=np.radians([40,75,30]);lo=np.radians([15,40,15]);hi=np.radians([70,85,65]);x=np.clip(old,lo,hi)
def apply(a):
 for b,v in zip(bones,a):b.rotation_euler.x=float(v)
 bpy.context.view_layer.update()
def residual(a):
 apply(a);return np.r_[point()-target,.0015*(a-prior)]
for iteration in range(18):
 r=residual(x);cols=[]
 for j in range(3):
  y=x.copy();y[j]+=.001;cols.append((residual(y)-r)/.001)
 J=np.array(cols).T;delta=np.linalg.solve(J.T@J+np.eye(3)*1e-7,-J.T@r);best=(float(r@r),x.copy())
 for rate in (1,.5,.25):
  y=np.clip(x+rate*delta,lo,hi);rr=residual(y)
  if float(rr@rr)<best[0]:best=(float(rr@rr),y)
 if np.linalg.norm(best[1]-x)<1e-5:break
 x=best[1]
apply(x);gap=float(np.linalg.norm(point()-target))
for m,v in sub:m.show_viewport=v
bpy.context.view_layer.update()
cam=s.camera;cb=cam.matrix_world.copy();cs=cam.data.ortho_scale;center=sum((pick.matrix_world@v.co for v in pick.data.vertices),Vector())/len(pick.data.vertices)
s.render.engine='BLENDER_WORKBENCH';s.render.resolution_x=900;s.render.resolution_y=900;s.render.resolution_percentage=100
try:
 for label,offset in [('front',(.13,-.2,.04)),('side',(-.12,-.18,.06))]:
  cam.location=center+Vector(offset);cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.14;s.render.filepath=str(out/(label+'.png'));bpy.ops.render.render(write_still=True)
finally:cam.matrix_world=cb;cam.data.ortho_scale=cs
report={'old_angles_deg':np.degrees(old).tolist(),'new_angles_deg':np.degrees(x).tolist(),'coarse_contact_patch_displacement_m':gap,'drivers':len(main.animation_data.drivers),'status':'INDEX_CURL_TRIAL_NOT_ACCEPTED'}
(out/'check.json').write_text(json.dumps(report,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(out/'Character_An_index_curl_TRIAL_v542.blend'));print(json.dumps(report))
