"""Preserve donor anatomy and native joints for isolated deformation review."""
import bpy,json,numpy as np,math
from pathlib import Path
from mathutils import Vector,Matrix
root=Path(__file__).resolve().parents[1];out=root/'production_v522_native_donor';out.mkdir(exist_ok=True)
original=bpy.context.window.scene;mainrig=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];assert len(mainrig.animation_data.drivers)==1957
assert not bpy.app.is_job_running('RENDER')
sb=json.loads((root/'production_v520_donor_fit/source_bones.json').read_text())['metarig-antonia']
scene=bpy.data.scenes.new('V522_NATIVE_REVIEW');bpy.context.window.scene=scene
with bpy.data.libraries.load(str(root/'production_v519_source_anatomy/Antonia_hand_donor_v519.blend'),link=False) as (src,dst):dst.objects=['V519_ANTONIA_HAND_DONOR']
o=dst.objects[0];o.name='V522_NATIVE_HAND';scene.collection.objects.link(o)
data=bpy.data.armatures.new('V522_NATIVE_JOINTS');rig=bpy.data.objects.new('V522_NATIVE_RIG',data);scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active=rig;rig.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
native={'DEF-Hand.R':'hand.L'}
for short,long in [('f_index','Index'),('f_middle','Middle'),('f_ring','Ring'),('f_pinky','Pinky'),('thumb','Thumb')]:
 for j in (1,2,3):native[f'DEF-Finger_{long}{j}.R']=f'{short}.{j:02d}.L'
for name,source in native.items():
 bone=data.edit_bones.new(name);s=sb[source];bone.head=s['head'];bone.tail=s['tail'];bone.align_roll(Matrix(s['matrix']).to_3x3().col[2])
 if name!='DEF-Hand.R':
  j=int(name[-3]);bone.parent=data.edit_bones['DEF-Hand.R' if j==1 else name[:-3]+str(j-1)+'.R']
bpy.ops.object.mode_set(mode='OBJECT')
# Reuse native sparse weight transfer, with identical destination naming.
code=(root/'pipeline/trial_v520_donor_fit.py').read_text();start=code.index("ids=json.loads");end=code.index("o.data.materials.clear()")
exec(compile(code[start:end],'<native weights>','exec'))
camdata=bpy.data.cameras.new('V522_CAMERA');cam=bpy.data.objects.new('V522_CAMERA',camdata);scene.collection.objects.link(cam);scene.camera=cam
world=bpy.data.worlds.new('V522_WORLD');scene.world=world;world.color=(.06,.06,.06)
scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.light='STUDIO';scene.display.shading.color_type='SINGLE';scene.display.shading.single_color=(.58,.44,.31);scene.display.shading.show_cavity=True;scene.display.shading.cavity_type='BOTH'
scene.render.resolution_x=900;scene.render.resolution_y=900;scene.render.resolution_percentage=100;camdata.type='ORTHO';camdata.ortho_scale=.29
w=Vector(sb['hand.L']['head']);along=(Vector(sb['f_middle.01.L']['head'])-w).normalized();across=(Vector(sb['f_index.01.L']['head'])-Vector(sb['f_pinky.01.L']['head'])).normalized();normal=across.cross(along).normalized()
center=sum((v.co for v in o.data.vertices),Vector())/len(o.data.vertices)
report=[]
try:
 for label,sign in [('open',0),('curl_positive',1),('curl_negative',-1)]:
  for name,source in native.items():
   if name=='DEF-Hand.R' or 'Thumb' in name:continue
   b=rig.pose.bones[name];direction=(b.bone.tail_local-b.bone.head_local).normalized();axis=normal.cross(direction).normalized();localaxis=b.bone.matrix_local.to_3x3().inverted()@axis
   angle=(40,65,30)[int(name[-3])-1];b.rotation_mode='AXIS_ANGLE';b.rotation_axis_angle=(math.radians(angle)*sign,*localaxis)
  bpy.context.view_layer.update()
  ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();finite=all(math.isfinite(c) for v in mesh.vertices for c in v.co);ev.to_mesh_clear()
  for side in (-1,1):
   cam.location=center+normal*side*.6;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(out/f'{label}_{side}.png');bpy.ops.render.render(write_still=True)
  report.append({'pose':label,'finite':finite})
 for bone in rig.pose.bones:bone.matrix_basis=Matrix.Identity(4)
 bpy.context.view_layer.update();bpy.data.libraries.write(str(out/'Antonia_native_hand_rig_v522.blend'),{o,rig},fake_user=True)
 (out/'review.json').write_text(json.dumps({'poses':report,'native_joint_count':len(native),'drivers_preserved':len(mainrig.animation_data.drivers),'character':bpy.data.filepath},indent=2))
finally:
 bpy.context.window.scene=original
 for obj in (o,rig,cam):bpy.data.objects.remove(obj,do_unlink=True)
 bpy.data.scenes.remove(scene)
print('V522 native anatomy/rig saved separately; character unchanged')
