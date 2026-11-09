"""Reversible native-thumb surface fit with bounded opposition and flexion."""
import bpy,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion
root=Path(__file__).resolve().parents[1];out=root/'production_v531_thumb_surface';out.mkdir(exist_ok=True)
scene=bpy.context.scene;rig=bpy.data.objects['V528_NATIVE_RIG.R'];hand=bpy.data.objects['V528_NATIVE_HAND.R'];main=bpy.data.objects['V357_CLOUDRIG_CONTROLS']
assert not bpy.app.is_job_running('RENDER') and len(main.animation_data.drivers)==1957
bones=[rig.pose.bones[f'DEF-Finger_Thumb{j}.R'] for j in (1,2,3)]
backup=[(b.rotation_mode,b.matrix_basis.copy()) for b in bones]
sub=[(m,m.show_viewport) for m in hand.modifiers if m.type=='SUBSURF']
s=rig.data.bones;along=(s['DEF-Finger_Middle1.R'].head_local-s['DEF-Hand.R'].head_local).normalized();across=(s['DEF-Finger_Index1.R'].head_local-s['DEF-Finger_Pinky1.R'].head_local).normalized();normal=across.cross(along).normalized()
axes=[b.bone.matrix_local.to_3x3().inverted()@normal.cross(b.bone.tail_local-b.bone.head_local).normalized() for b in bones]
opposition=bones[0].bone.matrix_local.to_3x3().inverted()@normal
indices=[v.index for v in hand.data.vertices if any(g.group==hand.vertex_groups['DEF-Finger_Thumb3.R'].index and g.weight>.55 for g in v.groups)]
assert len(indices)>10
pick=bpy.data.objects['V361_NYLON_PICK'].evaluated_get(bpy.context.evaluated_depsgraph_get());pts=np.array([list(pick.matrix_world@v.co) for v in pick.data.vertices]);center=pts.mean(axis=0);_,_,vt=np.linalg.svd(pts-center,full_matrices=False);n=vt[-1]
if np.dot(n,np.array(rig.matrix_world@bones[0].head)-center)<0:n=-n
thickness=max(abs((pts-center)@n));target=center+n*(thickness+.0002)
angles=[0.,0.,0.,0.];limits=[(-.65,.65),(-.8,.8),(-.15,1.1),(-.15,1.0)]
def apply():
 for j,b in enumerate(bones):
  b.rotation_mode='QUATERNION';b.rotation_quaternion=Quaternion(axes[j],angles[0 if j==0 else j+1])
  if j==0:b.rotation_quaternion=Quaternion(opposition,angles[1])@b.rotation_quaternion
 bpy.context.view_layer.update()
def sample():
 obj=hand.evaluated_get(bpy.context.evaluated_depsgraph_get());v=np.array([list(obj.matrix_world@obj.data.vertices[i].co) for i in indices]);d=np.linalg.norm(v-target,axis=1);return v,d

def objective():
 v,d=sample();nearest=np.sort(d)[:4]
 return float(np.mean(nearest**2)+.0000003*sum(a*a for a in angles))
cam=scene.camera;cb=cam.matrix_world.copy();ortho=cam.data.ortho_scale
settings=(scene.render.engine,scene.render.resolution_x,scene.render.resolution_y,scene.render.resolution_percentage,scene.render.filepath)
try:
 for m,_ in sub:m.show_viewport=False
 apply();before=objective()
 for step in (.24,.12,.06,.025):
  for sweep in range(3):
   for j in range(4):
    base=angles[j];best=(objective(),base)
    for sign in (-1,1):
     angles[j]=max(limits[j][0],min(limits[j][1],base+sign*step));apply();score=objective()
     if score<best[0]:best=(score,angles[j])
    angles[j]=best[1];apply()
 v,d=sample();report={'angles_deg':[math.degrees(a) for a in angles],'closest_thumb_vertex_gap_m':float(d.min()),'closest_thumb_vertex':indices[int(d.argmin())],'target':target.tolist(),'before':before,'after':objective(),'main_drivers':len(main.animation_data.drivers),'status':'TRIAL_SURFACE_FIT_REQUIRES_VISUAL_AND_COLLISION_REVIEW'}
 for m,enabled in sub:m.show_viewport=enabled
 bpy.context.view_layer.update()
 scene.render.engine='BLENDER_WORKBENCH';scene.render.resolution_percentage=100;scene.render.resolution_x=900;scene.render.resolution_y=900
 for label,pos,look,scale in [('instrument',(-.00624775,-.645,.74370837),(-.10234958,-.27,1.0314399),.42),('pinch',tuple(center+np.array((.13,-.2,.04))),tuple(center),.13)]:
  cam.location=pos;cam.rotation_euler=(Vector(look)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;scene.render.filepath=str(out/(label+'.png'));bpy.ops.render.render(write_still=True)
 (out/'fit.json').write_text(json.dumps(report,indent=2))
 bpy.ops.wm.save_as_mainfile(filepath=str(out/'Character_An_thumb_surface_TRIAL_v531.blend'),copy=True)
finally:
 for b,(mode,basis) in zip(bones,backup):b.rotation_mode=mode;b.matrix_basis=basis
 for m,enabled in sub:m.show_viewport=enabled
 cam.matrix_world=cb;cam.data.ortho_scale=ortho
 scene.render.engine,scene.render.resolution_x,scene.render.resolution_y,scene.render.resolution_percentage,scene.render.filepath=settings
 bpy.context.view_layer.update()
print(json.dumps(report));print('V528 restored')
