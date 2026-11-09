"""Review locally available hand source topology without editing the character."""
import bpy,json
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1];out=root/'production_v519_source_anatomy';out.mkdir(exist_ok=True)
original=bpy.context.window.scene
rig=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];assert len(rig.animation_data.drivers)==1957
assert not bpy.app.is_job_running('RENDER')
scene=bpy.data.scenes.new('V519_SOURCE_REVIEW');world=bpy.data.worlds.new('V519_WORLD');scene.world=world;world.color=(.06,.06,.06)
camdata=bpy.data.cameras.new('V519_CAMERA');cam=bpy.data.objects.new('V519_CAMERA',camdata);scene.collection.objects.link(cam);scene.camera=cam
scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.light='STUDIO';scene.display.shading.color_type='SINGLE';scene.display.shading.single_color=(.58,.44,.31)
scene.display.shading.show_cavity=True;scene.display.shading.cavity_type='BOTH';scene.display.shading.background_type='WORLD'
scene.render.resolution_x=1000;scene.render.resolution_y=800;scene.render.resolution_percentage=100
camdata.type='ORTHO';camdata.ortho_scale=.30
report=[]
bpy.context.window.scene=scene
try:
 for name in ['mb_male','antonia']:
  with bpy.data.libraries.load(str(root/'third_party/charmorph/v0.4.0-3/CharMorph-data/characters'/name/'char.blend'),link=False) as (src,dst):dst.objects=src.objects
  objects=[o for o in dst.objects if o];source=max((o for o in objects if o.type=='MESH'),key=lambda o:len(o.data.vertices))
  ids=[v.index for v in source.data.vertices if v.co.x>.57];mapping={v:i for i,v in enumerate(ids)}
  coords=[tuple(source.data.vertices[i].co) for i in ids]
  faces=[[mapping[i] for i in p.vertices] for p in source.data.polygons if all(i in mapping for i in p.vertices)]
  mesh=bpy.data.meshes.new('V519_HAND');mesh.from_pydata(coords,[],faces);mesh.update()
  obj=bpy.data.objects.new('V519_HAND',mesh);scene.collection.objects.link(obj)
  for p in mesh.polygons:p.use_smooth=True
  mod=obj.modifiers.new('Source subdivision','SUBSURF');mod.levels=2
  center=Vector(tuple((min(c[i] for c in coords)+max(c[i] for c in coords))/2 for i in range(3)))
  for label,direction in [('front',Vector((0,-1,.25))),('back',Vector((0,1,.25)))]:
   cam.location=center+direction.normalized()*.7;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(out/(name+'_'+label+'.png'));bpy.ops.render.render(write_still=True)
  report.append({'source':name,'vertices':len(coords),'faces':len(faces)})
  bpy.data.objects.remove(obj,do_unlink=True);bpy.data.meshes.remove(mesh)
  for o in objects:
   data=o.data;typ=o.type;bpy.data.objects.remove(o,do_unlink=True)
   if typ=='MESH' and data.users==0:bpy.data.meshes.remove(data)
finally:
 bpy.context.window.scene=original;bpy.data.scenes.remove(scene);bpy.data.objects.remove(cam,do_unlink=True);bpy.data.cameras.remove(camdata);bpy.data.worlds.remove(world)
(out/'review.json').write_text(json.dumps({'sources':report,'character_file':bpy.data.filepath,'drivers':len(rig.animation_data.drivers)},indent=2))
print('V519 source comparison complete; character unchanged')
