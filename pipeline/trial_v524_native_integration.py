"""Attach unwarped native donor rig to existing wrist; save isolated integration trial."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector,Matrix
root=Path(__file__).resolve().parents[1];out=root/'production_v524_native_integration';out.mkdir(exist_ok=True)
main=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];old=bpy.data.objects['V357_ANATOMICAL_HAND.R'];scene=bpy.context.scene
assert len(main.animation_data.drivers)==1957 and not bpy.app.is_job_running('RENDER')
with bpy.data.libraries.load(str(root/'production_v522_native_donor/Antonia_native_hand_rig_v522.blend'),link=False) as (src,dst):dst.objects=['V522_NATIVE_HAND','V522_NATIVE_RIG']
for obj in dst.objects:scene.collection.objects.link(obj)
o=next(x for x in dst.objects if x.type=='MESH');rig=next(x for x in dst.objects if x.type=='ARMATURE');o.name='V524_NATIVE_HAND.R';rig.name='V524_NATIVE_RIG.R'
def frame(w,m,i,p):
 y=(m-w).normalized();x=i-p;x=(x-y*x.dot(y)).normalized();z=x.cross(y).normalized()
 return Matrix((x,y,z)).transposed(),(m-w).length
s=rig.data.bones;t=main.data.bones
sf,sl=frame(s['DEF-Hand.R'].head_local,s['DEF-Finger_Middle1.R'].head_local,s['DEF-Finger_Index1.R'].head_local,s['DEF-Finger_Pinky1.R'].head_local)
tf,tl=frame(t['DEF-Hand.R'].head_local,t['DEF-Finger_Middle1.R'].head_local,t['DEF-Finger_Index1.R'].head_local,t['DEF-Finger_Pinky1.R'].head_local)
scale=tl/sl
alignment=(tf@sf.inverted()).to_4x4()@Matrix.Scale(scale,4)
alignment.translation=t['DEF-Hand.R'].head_local-alignment.to_3x3()@s['DEF-Hand.R'].head_local
world=main.matrix_world@main.pose.bones['DEF-Hand.R'].matrix@t['DEF-Hand.R'].matrix_local.inverted()@alignment
rig.parent=main;rig.parent_type='BONE';rig.parent_bone='DEF-Hand.R';bpy.context.view_layer.update();rig.matrix_world=world
o.parent=rig;o.matrix_parent_inverse=Matrix.Identity(4);o.matrix_basis=Matrix.Identity(4)
normal=sf.col[2]
for f in ('Index','Middle','Ring','Pinky'):
 for j in (1,2,3):
  name=f'DEF-Finger_{f}{j}.R';b=rig.pose.bones[name];axis=normal.cross(b.bone.tail_local-b.bone.head_local).normalized();axis=b.bone.matrix_local.to_3x3().inverted()@axis
  b.rotation_mode='AXIS_ANGLE';b.rotation_axis_angle=(0,*axis)
  d=b.driver_add('rotation_axis_angle',0).driver;v=d.variables.new();v.name='flex';v.type='SINGLE_PROP';v.targets[0].id=main;v.targets[0].data_path=f'pose.bones["FK-Finger_{f}{j}.R"].rotation_euler[0]';d.expression='flex'
o.data.materials.clear()
for mat in old.data.materials:o.data.materials.append(mat)
for poly in o.data.polygons:poly.material_index=1 if poly.material_index in (5,6) else 0
visibility=(old.hide_render,old.hide_get());old.hide_render=True;old.hide_set(True)
bpy.context.view_layer.update()
try:
 f=root/'pipeline/review_v492_isolated_palm.py';code=f.read_text().replace("bpy.data.objects['V357_ANATOMICAL_HAND.R']","bpy.data.objects['V524_NATIVE_HAND.R']").replace('production_v492_palm_review','production_v524_native_integration')
 code=code.replace('points=[obj.matrix_world@v.co for v in mesh.vertices]', 'bpy.context.window.scene=scene; bpy.context.view_layer.update()\npoints=[obj.matrix_world@v.co for v in mesh.vertices]')
 exec(compile(code,str(f),'exec'),{'__file__':str(f)})
 # Save a review-only full integration copy; retain the existing authoritative file.
 bpy.ops.wm.save_as_mainfile(filepath=str(out/'Character_An_native_hand_integration_TRIAL_v524.blend'),copy=True)
 (out/'integration.json').write_text(json.dumps({'uniform_rest_scale':scale,'main_drivers':len(main.animation_data.drivers),'donor_drivers':len(rig.animation_data.drivers),'source_character':bpy.data.filepath,'thumb':'native open, not yet fitted','status':'TRIAL_REQUIRES_VISUAL_REVIEW'},indent=2))
finally:
 old.hide_render=visibility[0];old.hide_set(visibility[1])
 bpy.data.objects.remove(o,do_unlink=True);bpy.data.objects.remove(rig,do_unlink=True);bpy.context.view_layer.update()
print('V524 integration copy saved; original character restored')
