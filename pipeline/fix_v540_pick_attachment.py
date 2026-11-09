"""Attach plectrum to the native deform hand, preserving its fitted world pose."""
import bpy,json,math
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
root=Path(__file__).resolve().parents[1];out=root/'production_v540_pick_attachment';out.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(root/'production_v538_pick_tip/Character_An_pick_tip_TRIAL_v538.blend'))
s=bpy.context.scene;main=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];rig=bpy.data.objects['V528_NATIVE_RIG.R'];pick=bpy.data.objects['V361_NYLON_PICK'];hand=bpy.data.objects['V528_NATIVE_HAND.R'];c=main.pose.bones['IK-Hand.R'];cam=s.camera
assert len(main.animation_data.drivers)==1957
original=c.matrix.copy();pb=pick.matrix_world.copy();cb=cam.matrix_world.copy();cs=cam.data.ortho_scale
old_parent={'object':pick.parent.name,'bone':pick.parent_bone}
pick.parent=rig;pick.parent_type='BONE';pick.parent_bone='DEF-Hand.R';pick.matrix_parent_inverse=Matrix.Identity(4)
bpy.context.view_layer.update()
parent_frame=rig.matrix_world@rig.pose.bones['DEF-Hand.R'].matrix@Matrix.Translation((0,rig.data.bones['DEF-Hand.R'].length,0))
pick.matrix_parent_inverse=parent_frame.inverted()@pb;pick.matrix_basis=Matrix.Identity(4);bpy.context.view_layer.update()
def frame():return rig.matrix_world@rig.pose.bones['DEF-Hand.R'].matrix
def difference(a,b):return max(abs(a[i][j]-b[i][j]) for i in range(4) for j in range(4))
relative=frame().inverted()@pick.matrix_world
initial_error=difference(pb,pick.matrix_world);assert initial_error<1e-5,initial_error
samples=[]
try:
 for angle,offset in [(0,(0,0,0)),(15,(0,0,.025)),(-15,(.015,0,.02))]:
  mat=original.copy();loc=mat.translation.copy();mat=Quaternion(Vector((0,0,1)),math.radians(angle)).to_matrix().to_4x4()@mat;mat.translation=loc+Vector(offset);c.matrix=mat;bpy.context.view_layer.update()
  error=difference(relative,frame().inverted()@pick.matrix_world);samples.append({'angle_degrees':angle,'offset':offset,'relative_matrix_error':error});assert error<1e-5,error
 c.matrix=original;bpy.context.view_layer.update()
 s.render.engine='BLENDER_WORKBENCH';s.render.resolution_x=900;s.render.resolution_y=900;s.render.resolution_percentage=100
 center=sum((pick.matrix_world@v.co for v in pick.data.vertices),Vector())/len(pick.data.vertices)
 for label,pos,target,scale in [('pinch',tuple(center+Vector((.13,-.2,.04))),tuple(center),.16),('instrument',(-.00624775,-.645,.74370837),(-.10234958,-.27,1.0614399),.42)]:
  cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;s.render.filepath=str(out/(label+'.png'));bpy.ops.render.render(write_still=True)
finally:
 c.matrix=original;cam.matrix_world=cb;cam.data.ortho_scale=cs;bpy.context.view_layer.update()
report={'old_parent':old_parent,'new_parent':{'object':pick.parent.name,'bone':pick.parent_bone},'initial_world_matrix_error':initial_error,'motion_checks':samples,'drivers':len(main.animation_data.drivers),'status':'ATTACHMENT_FIXED_GRIP_NOT_FINAL'}
(out/'check.json').write_text(json.dumps(report,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(out/'Character_An_pick_attachment_v540.blend'))
print(json.dumps(report))
