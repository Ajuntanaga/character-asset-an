"""Bounded native thumb hinge fitting and local visual review, retaining V528."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
import numpy as np
root=Path(__file__).resolve().parents[1];out=root/'production_v530_thumb_hinges';out.mkdir(exist_ok=True)
scene=bpy.context.scene;rig=bpy.data.objects['V528_NATIVE_RIG.R'];main=bpy.data.objects['V357_CLOUDRIG_CONTROLS']
assert not bpy.app.is_job_running('RENDER') and len(main.animation_data.drivers)==1957
bones=[rig.pose.bones[f'DEF-Finger_Thumb{j}.R'] for j in (1,2,3)]
backup=[(b.rotation_mode,b.matrix_basis.copy()) for b in bones]
s=rig.data.bones
along=(s['DEF-Finger_Middle1.R'].head_local-s['DEF-Hand.R'].head_local).normalized()
across=(s['DEF-Finger_Index1.R'].head_local-s['DEF-Finger_Pinky1.R'].head_local).normalized();normal=across.cross(along).normalized()
axes=[b.bone.matrix_local.to_3x3().inverted()@normal.cross(b.bone.tail_local-b.bone.head_local).normalized() for b in bones]
pick=bpy.data.objects['V361_NYLON_PICK'].evaluated_get(bpy.context.evaluated_depsgraph_get());pts=np.array([list(pick.matrix_world@v.co) for v in pick.data.vertices]);center=Vector(pts.mean(axis=0));_,_,vt=np.linalg.svd(pts-pts.mean(axis=0),full_matrices=False);n=Vector(vt[-1])
if n.dot(rig.matrix_world@bones[0].head-center)<0:n=-n
target=center+n*.005
angles=[0.,0.,0.];limits=[(-.6,.6),(-.17,1.1),(-.17,1.1)]
def apply():
 for b,a,axis in zip(bones,angles,axes):b.rotation_mode='AXIS_ANGLE';b.rotation_axis_angle=(a,*axis)
 bpy.context.view_layer.update()
def objective():return ((rig.matrix_world@bones[-1].tail)-target).length_squared+sum(a*a for a in angles)*.000003
camera=scene.camera;cam_backup=camera.matrix_world.copy();ortho=camera.data.ortho_scale
settings=(scene.render.engine,scene.render.resolution_x,scene.render.resolution_y,scene.render.resolution_percentage,scene.render.filepath)
try:
 apply();before=objective()
 for step in (.25,.12,.05,.02):
  for sweep in range(3):
   for j in range(3):
    base=angles[j];best=(objective(),base)
    for sign in (-1,1):
     angles[j]=max(limits[j][0],min(limits[j][1],base+sign*step));apply();score=objective()
     if score<best[0]:best=(score,angles[j])
    angles[j]=best[1];apply()
 scene.render.engine='BLENDER_WORKBENCH';scene.render.resolution_percentage=100;scene.render.resolution_x=900;scene.render.resolution_y=900
 camera.location=(-.00624775,-.645,.74370837);camera.rotation_euler=(Vector((-.10234958,-.27,1.0314399))-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=.42
 scene.render.filepath=str(out/'instrument.png');bpy.ops.render.render(write_still=True)
 (out/'fit.json').write_text(json.dumps({'angles_degrees':[math.degrees(a) for a in angles],'tail_error_m':((rig.matrix_world@bones[-1].tail)-target).length,'before_objective':before,'after_objective':objective(),'main_drivers':len(main.animation_data.drivers),'status':'VISUAL_REVIEW_REQUIRED_SURFACE_CONTACT_UNVERIFIED'},indent=2))
 bpy.ops.wm.save_as_mainfile(filepath=str(out/'Character_An_thumb_hinges_TRIAL_v530.blend'),copy=True)
finally:
 for b,(mode,basis) in zip(bones,backup):b.rotation_mode=mode;b.matrix_basis=basis
 camera.matrix_world=cam_backup;camera.data.ortho_scale=ortho
 scene.render.engine,scene.render.resolution_x,scene.render.resolution_y,scene.render.resolution_percentage,scene.render.filepath=settings
 bpy.context.view_layer.update()
print('V530 saved; V528 pose restored')
