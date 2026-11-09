"""Add independent animation-ready wet eye geometry to the V334 head."""
from pathlib import Path
import hashlib,json,math
import bpy
from mathutils import Vector
ROOT=Path('/home/ajuntanaga/Projects/Blender/Character Asset_An');SOURCE=ROOT/'production_v334_groom_projection_cleanup'/'Character_An_groom_projection_cleanup_v334.blend'
STAGE=ROOT/'production_v335_wet_eye_geometry';OUTPUT=STAGE/'Character_An_wet_eye_geometry_v335.blend';RENDERS=STAGE/'renders';AUDIT=STAGE/'audit'/'v335_wet_eye_geometry.json'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def mat(name,color,rough=.35,metal=0.0):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
 if 'Specular IOR Level' in p.inputs:p.inputs['Specular IOR Level'].default_value=.42
 return m
def cornea_mat():
 m=bpy.data.materials.new('V335_CORNEA');m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(1,1,1,1);p.inputs['Roughness'].default_value=.045;p.inputs['Transmission Weight'].default_value=1.0;p.inputs['IOR'].default_value=1.376;p.inputs['Alpha'].default_value=.18;m.surface_render_method='DITHERED';return m
def parent_bone(o,rig,bone):
 w=o.matrix_world.copy();o.parent=rig;o.parent_type='BONE';o.parent_bone=bone;o.matrix_world=w
def sphere(name,loc,radius,material,rig,bone):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=64,ring_count=32,location=loc,radius=radius);o=bpy.context.object;o.name=name;o.data.materials.append(material);bpy.ops.object.shade_smooth();parent_bone(o,rig,bone);return o
def disc(name,loc,radius,depth,material,rig,bone):
 bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=radius,depth=depth,location=loc,rotation=(math.pi/2,0,0));o=bpy.context.object;o.name=name;o.data.materials.append(material);bpy.ops.object.shade_smooth();parent_bone(o,rig,bone);return o
def aim(o,t):o.rotation_euler=(t-o.location).to_track_quat('-Z','Y').to_euler()
def render(s,c,p,l,t,lens):c.location=l;c.data.lens=lens;aim(c,t);s.camera=c;s.render.resolution_x=s.render.resolution_y=900;s.render.resolution_percentage=100;s.render.filepath=str(p);bpy.ops.render.render(write_still=True);return {'path':str(p.relative_to(ROOT)),'sha256':sha(p)}
def main():
 bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
 for p in (STAGE,RENDERS,AUDIT.parent):p.mkdir(parents=True,exist_ok=True)
 rig=bpy.data.objects['V322_MB_MALE_RIG'];sclera=mat('V335_SCLERA',(0.78,0.70,0.62),.28);iris=mat('V335_IRIS_DARK_BROWN',(0.018,0.0065,0.0025),.24);pupil=mat('V335_PUPIL',(0.00005,0.00005,0.00005),.18);cornea=cornea_mat();objects=[]
 for label,x,bone in (('L',-.034,'eye.L'),('R',.034,'eye.R')):
  center=(x,-.1515,1.692);objects.append(sphere(f'V335_EYEBALL_{label}',center,.0128,sclera,rig,bone));objects.append(disc(f'V335_IRIS_{label}',(x,-.1639,1.692),.00525,.00065,iris,rig,bone));objects.append(disc(f'V335_PUPIL_{label}',(x,-.16435,1.692),.00235,.00035,pupil,rig,bone));objects.append(sphere(f'V335_CORNEA_{label}',(x,-.1524,1.692),.01305,cornea,rig,bone))
 scene=bpy.context.scene;scene['V335_STATUS']='WET_EYE_GEOMETRY_VISUAL_REVIEW_REQUIRED';cam=bpy.data.objects['V323_CAMERA'];target=Vector((0,-.065,1.675));renders={'front':render(scene,cam,RENDERS/'v335_eyes_front.png',Vector((0,-1.28,1.69)),target,112),'three_quarter':render(scene,cam,RENDERS/'v335_eyes_three_quarter.png',Vector((.58,-1.16,1.71)),target,106),'eye_closeup':render(scene,cam,RENDERS/'v335_eye_closeup.png',Vector((0,-.82,1.70)),Vector((0,-.12,1.692)),118)}
 bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT),check_existing=False);rec={'schema':'v335-wet-eye-geometry-v1','status':'BUILT_VISUAL_REVIEW_REQUIRED','source':{'path':str(SOURCE.relative_to(ROOT)),'sha256':sha(SOURCE)},'objects':[o.name for o in objects],'renders':renders,'output':{'path':str(OUTPUT.relative_to(ROOT)),'sha256':sha(OUTPUT)}};AUDIT.write_text(json.dumps(rec,indent=2,sort_keys=True)+'\n');print('V335_WET_EYES_OK='+json.dumps(rec['output'],sort_keys=True))
if __name__=='__main__':main()
