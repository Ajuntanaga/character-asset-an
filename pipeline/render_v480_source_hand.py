import bpy,json
from mathutils import Vector
from pathlib import Path
root=Path('/home/ajuntanaga/Projects/Blender/Character Asset_An');out=root/'production_v480_hand_source_review'
s=bpy.data.scenes['V480_SOURCE_REVIEW'];bpy.context.window.scene=s
for o in s.objects:
 if o.name=='Icosphere':o.hide_render=True
hand=s.objects['Avery | anatomical body'];rig=s.objects['Avery | anatomical body.rig']
rig.data.pose_position='REST'
bpy.context.view_layer.update()
pts=[hand.matrix_world@Vector(c) for c in hand.bound_box];center=sum(pts,Vector())/8
mat=bpy.data.materials.new('V480_review_clay');mat.diffuse_color=(.4,.25,.16,1);hand.data.materials.clear();hand.data.materials.append(mat)
cam=bpy.data.objects.new('V480_Camera',bpy.data.cameras.new('V480_Camera'));s.collection.objects.link(cam);s.camera=cam
cam.location=center+Vector((.4,-.4,.4));cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=.32
s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.color_type='MATERIAL';s.display.shading.show_shadows=True;s.display.shading.show_cavity=True
s.render.resolution_x=800;s.render.resolution_y=800;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.filepath=str(out/'source_rest.png')
(out/'rig.json').write_text(json.dumps({'bones':[b.name for b in rig.data.bones],'mesh_vertices':len(hand.data.vertices),'mesh_polygons':len(hand.data.polygons)},indent=2))
bpy.ops.render.render('INVOKE_DEFAULT',write_still=True)
print('Source review render started')
