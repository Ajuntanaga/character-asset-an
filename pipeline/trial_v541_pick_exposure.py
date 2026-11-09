"""Compare bounded plectrum slides while retaining the deform-bone attachment."""
import bpy,json
from pathlib import Path
from mathutils import Vector,Matrix
root=Path(__file__).resolve().parents[1];out=root/'production_v541_pick_exposure';out.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(root/'production_v540_pick_attachment/Character_An_pick_attachment_v540.blend'))
s=bpy.context.scene;pick=bpy.data.objects['V361_NYLON_PICK'];rig=pick.parent;main=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];cam=s.camera
base=pick.matrix_world.copy();inv=pick.matrix_parent_inverse.copy();cb=cam.matrix_world.copy();cs=cam.data.ortho_scale
pts=[base@v.co for v in pick.data.vertices];center=sum(pts,Vector())/len(pts);tip=(pts[0]+pts[48])/2;back=(pts[24]+pts[72])/2;axis=(tip-back).normalized()
parent=rig.matrix_world@rig.pose.bones[pick.parent_bone].matrix@Matrix.Translation((0,rig.data.bones[pick.parent_bone].length,0))
s.render.engine='BLENDER_WORKBENCH';s.render.resolution_x=900;s.render.resolution_y=900;s.render.resolution_percentage=100
try:
 for mm in (3,6):
  pick.matrix_parent_inverse=parent.inverted()@Matrix.Translation(axis*(mm/1000))@base;pick.matrix_basis=Matrix.Identity(4);bpy.context.view_layer.update()
  for label,offset in [('front',(.13,-.2,.04)),('side',(-.12,-.18,.06))]:
   cam.location=center+Vector(offset);cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.14;s.render.filepath=str(out/f'{label}_{mm}mm.png');bpy.ops.render.render(write_still=True)
 (out/'check.json').write_text(json.dumps({'slides_mm':[3,6],'drivers':len(main.animation_data.drivers),'parent':rig.name,'bone':pick.parent_bone,'status':'VISUAL_COMPARISON_NOT_ACCEPTED'},indent=2))
finally:
 pick.matrix_parent_inverse=inv;cam.matrix_world=cb;cam.data.ortho_scale=cs;bpy.context.view_layer.update()
print('V541 exposure comparison rendered; V540 restored without saving trial geometry')
