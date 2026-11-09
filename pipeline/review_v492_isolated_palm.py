"""Render evaluated picking hand in isolation without changing the character scene."""
import bpy,json
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1]
out=root/'production_v492_palm_review';out.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
original=bpy.context.window.scene
rig=bpy.data.objects['V357_CLOUDRIG_CONTROLS']
assert len(rig.animation_data.drivers)==1957
hand=bpy.data.objects['V357_ANATOMICAL_HAND.R']
evaluated=hand.evaluated_get(bpy.context.evaluated_depsgraph_get())
mesh=bpy.data.meshes.new_from_object(evaluated)
scene=bpy.data.scenes.new('V492_TEMP_HAND_REVIEW')
obj=bpy.data.objects.new('V492_EVALUATED_HAND',mesh);scene.collection.objects.link(obj);obj.matrix_world=hand.matrix_world
camdata=bpy.data.cameras.new('V492_REVIEW');cam=bpy.data.objects.new('V492_REVIEW',camdata);scene.collection.objects.link(cam);scene.camera=cam
points=[obj.matrix_world@v.co for v in mesh.vertices]
center=Vector(tuple((min(p[i] for p in points)+max(p[i] for p in points))/2 for i in range(3)))
# Hand local palm normal follows its deformed hand bone, not the rest object frame.
bone=rig.pose.bones['DEF-Hand.R']
frame=(rig.matrix_world@bone.matrix).to_3x3()
normal=(frame@Vector((1,0,0))).normalized()
scene.render.engine='BLENDER_WORKBENCH'
scene.display.shading.light='STUDIO';scene.display.shading.color_type='SINGLE'
scene.display.shading.single_color=(.58,.44,.31)
scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True
scene.display.shading.cavity_type='BOTH';scene.display.shading.background_type='WORLD'
scene.world=bpy.data.worlds.new('V492_WORLD');scene.world.color=(.06,.06,.06)
scene.render.resolution_x=900;scene.render.resolution_y=900;scene.render.resolution_percentage=100
camdata.type='ORTHO';camdata.ortho_scale=.38
bpy.context.window.scene=scene
try:
 for label,direction in [('across_a',normal),('across_b',-normal)]:
  cam.location=center+direction*.6
  cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
  scene.render.filepath=str(out/(label+'.png'))
  bpy.ops.render.render(write_still=True)
 (out/'report.json').write_text(json.dumps({'source':bpy.data.filepath,'vertices':len(mesh.vertices),'drivers':len(rig.animation_data.drivers),'normal':list(normal)},indent=2))
finally:
 bpy.context.window.scene=original
 world=scene.world
 bpy.data.scenes.remove(scene)
 bpy.data.objects.remove(obj,do_unlink=True);bpy.data.objects.remove(cam,do_unlink=True)
 bpy.data.meshes.remove(mesh);bpy.data.cameras.remove(camdata);bpy.data.worlds.remove(world)
print('V492 review complete; original scene restored')
