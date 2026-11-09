"""Fit fixed anatomical thumb-pad and radial-index patches with bounded joints."""
import bpy,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion,Matrix
root=Path(__file__).resolve().parents[1];out=root/'production_v537_opposed_contact';out.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(root/'production_v535_reachable_wrist/Character_An_wrist_clearance_TRIAL_v535.blend'))
scene=bpy.context.scene;main=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];rig=bpy.data.objects['V528_NATIVE_RIG.R'];hand=bpy.data.objects['V528_NATIVE_HAND.R'];pick=bpy.data.objects['V361_NYLON_PICK']
assert len(main.animation_data.drivers)==1957 and not bpy.app.is_job_running('RENDER')
thumb=[rig.pose.bones[f'DEF-Finger_Thumb{j}.R'] for j in (1,2,3)]
index=[main.pose.bones[f'FK-Finger_Index{j}.R'] for j in (1,2,3)]
backup=[(b,b.rotation_mode,b.matrix_basis.copy()) for b in thumb+index];pb=pick.matrix_world.copy()
sub=[(m,m.show_viewport) for m in hand.modifiers if m.type=='SUBSURF']
s=rig.data.bones;along=(s['DEF-Finger_Middle1.R'].head_local-s['DEF-Hand.R'].head_local).normalized();across=(s['DEF-Finger_Index1.R'].head_local-s['DEF-Finger_Pinky1.R'].head_local).normalized();normal=across.cross(along).normalized()
axes=[b.bone.matrix_local.to_3x3().inverted()@normal.cross(b.bone.tail_local-b.bone.head_local).normalized() for b in thumb];opposition=thumb[0].bone.matrix_local.to_3x3().inverted()@normal
nails={i for p in hand.data.polygons if p.material_index==1 for i in p.vertices}
def weighted(name):
 g=hand.vertex_groups[name].index
 return [v.index for v in hand.data.vertices if any(x.group==g and x.weight>.6 for x in v.groups)]
def patch(name,radial):
 b=s[name];axis=(b.tail_local-b.head_local).normalized();length=(b.tail_local-b.head_local).length
 ids=[i for i in weighted(name) if i not in nails and .25*length<(hand.data.vertices[i].co-b.head_local).dot(axis)<.85*length]
 assert len(ids)>=6,(name,len(ids))
 radial=(radial-axis*radial.dot(axis)).normalized()
 return sorted(ids,key=lambda i:(hand.data.vertices[i].co-b.head_local).dot(radial),reverse=True)[:8]
b=s['DEF-Finger_Thumb3.R'];ni=[i for i in weighted(b.name) if i in nails];assert ni
nailcenter=sum((hand.data.vertices[i].co for i in ni),Vector())/len(ni)
tp=patch(b.name,b.head_local-nailcenter)
ib=s['DEF-Finger_Index3.R'];ip=patch(ib.name,s['DEF-Finger_Thumb3.R'].head_local-ib.head_local)
pts=np.array([list(pick.matrix_world@v.co) for v in pick.data.vertices]);pc=pts.mean(axis=0);_,_,vt=np.linalg.svd(pts-pc,full_matrices=False);pn=Vector(vt[-1]);thickness=np.ptp((pts-pc)@vt[-1]);assert thickness<.005
x=np.array([.215,.215,.215,.095]+[b.rotation_euler.x for b in index]);prior=x.copy()
lo=np.array([-.65,-.8,-.15,-.15,.1,.4,0]);hi=np.array([.65,.8,1.1,1.,1.3,1.8,1.2])
def apply(a):
 for j,b in enumerate(thumb):
  b.rotation_mode='QUATERNION';b.rotation_quaternion=Quaternion(axes[j],a[0 if j==0 else j+1])
  if j==0:b.rotation_quaternion=Quaternion(opposition,a[1])@b.rotation_quaternion
 for j,b in enumerate(index):b.rotation_euler.x=a[j+4]
 bpy.context.view_layer.update()
def surface(ids):
 e=hand.evaluated_get(bpy.context.evaluated_depsgraph_get());nm=e.matrix_world.to_3x3().inverted().transposed()
 return np.mean([list(e.matrix_world@e.data.vertices[i].co) for i in ids],axis=0),np.array(sum((nm@e.data.vertices[i].normal for i in ids),Vector()).normalized())
def residual(a):
 apply(a);t,tn=surface(tp);i,inn=surface(ip)
 return np.r_[(t-i-inn*(thickness+.0004)),.004*(tn+inn),.0005*(a-prior)]
cam=scene.camera;cb=cam.matrix_world.copy();cs=cam.data.ortho_scale
settings=(scene.render.engine,scene.render.resolution_x,scene.render.resolution_y,scene.render.resolution_percentage,scene.render.filepath)
try:
 for m,_ in sub:m.show_viewport=False
 initial=residual(x);iterations=0
 for step in (.2,.1,.05,.025,.012):
  for sweep in range(4):
   changed=False
   for j in range(7):
    r=residual(x);best=(float(r@r),x.copy())
    for sign in (-1,1):
     candidate=x.copy();candidate[j]=np.clip(x[j]+sign*step,lo[j],hi[j]);rr=residual(candidate)
     if float(rr@rr)<best[0]:best=(float(rr@rr),candidate)
    changed=changed or np.linalg.norm(best[1]-x)>1e-6;x=best[1];iterations+=1
   if not changed:break
 apply(x);t,tn=surface(tp);i,inn=surface(ip);seat=(t+i)/2
 # Orient pick normal between the fixed anatomical contact patches.
 n=Vector(inn).normalized();rotation=pn.rotation_difference(n).to_matrix().to_4x4()
 pick.matrix_world=Matrix.Translation(Vector(seat))@rotation@Matrix.Translation(-Vector(pc))@pb
 report={'thumb_patch':tp,'index_radial_patch':ip,'angles_deg':np.degrees(x).tolist(),'patch_separation_m':float(np.linalg.norm(t-i)),'pick_thickness_m':float(thickness),'normal_dot':float(tn@inn),'contact_residual_m':float(np.linalg.norm(t-i-inn*(thickness+.0004))),'iterations':iterations,'drivers':len(main.animation_data.drivers),'status':'OPPOSED_PATCH_TRIAL_REQUIRES_VISUAL_REVIEW'}
 for m,enabled in sub:m.show_viewport=enabled
 bpy.context.view_layer.update()
 scene.render.engine='BLENDER_WORKBENCH';scene.render.resolution_x=900;scene.render.resolution_y=900;scene.render.resolution_percentage=100
 for label,pos,target,scale in [('instrument',(-.00624775,-.645,.74370837),(-.10234958,-.27,1.0614399),.42),('pinch',tuple(Vector(seat)+Vector((.13,-.2,.04))),tuple(seat),.16)]:
  cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;scene.render.filepath=str(out/(label+'.png'));bpy.ops.render.render(write_still=True)
 (out/'contact.json').write_text(json.dumps(report,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(out/'Character_An_opposed_contact_TRIAL_v537.blend'),copy=True)
finally:
 for b,mode,basis in backup:b.rotation_mode=mode;b.matrix_basis=basis
 for m,enabled in sub:m.show_viewport=enabled
 pick.matrix_world=pb;cam.matrix_world=cb;cam.data.ortho_scale=cs
 scene.render.engine,scene.render.resolution_x,scene.render.resolution_y,scene.render.resolution_percentage,scene.render.filepath=settings
 bpy.context.view_layer.update()
print(json.dumps(report));print('V535 restored')
