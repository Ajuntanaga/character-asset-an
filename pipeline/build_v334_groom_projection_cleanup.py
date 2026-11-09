"""Refine V333 curl silhouette and replace unusable rear photo projections."""
from pathlib import Path
import hashlib, json
import bpy
from mathutils import Vector

ROOT=Path('/home/ajuntanaga/Projects/Blender/Character Asset_An')
SOURCE=ROOT/'production_v333_scalp_following_curl_groom'/'Character_An_scalp_following_curl_groom_v333.blend'
STAGE=ROOT/'production_v334_groom_projection_cleanup'; OUTPUT=STAGE/'Character_An_groom_projection_cleanup_v334.blend'
RENDERS=STAGE/'renders'; AUDIT=STAGE/'audit'/'v334_groom_projection_cleanup.json'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''): h.update(b)
 return h.hexdigest()
def aim(o,t): o.rotation_euler=(t-o.location).to_track_quat('-Z','Y').to_euler()
def render(s,c,p,l,t,lens):
 c.location=l;c.data.lens=lens;aim(c,t);s.camera=c;s.render.resolution_x=s.render.resolution_y=900;s.render.resolution_percentage=100;s.render.filepath=str(p);bpy.ops.render.render(write_still=True);return {'path':str(p.relative_to(ROOT)),'sha256':sha(p)}
def matte(name,color,roughness=0.72):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
 p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=roughness;p.inputs['Metallic'].default_value=0
 if 'Specular IOR Level' in p.inputs:p.inputs['Specular IOR Level'].default_value=0.20
 return m
def main():
 bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
 for p in (STAGE,RENDERS,AUDIT.parent):p.mkdir(parents=True,exist_ok=True)
 head=bpy.data.objects['V326_PHOTOREAL_FACEBUILDER_HEAD'];scalp=matte('V334_REAR_SCALP_MATTE',(0.003,0.004,0.006),0.82);neck=matte('V334_REAR_NECK_SKIN',(0.26,0.105,0.055),0.56)
 head.data.materials.append(scalp);scalp_i=len(head.data.materials)-1;head.data.materials.append(neck);neck_i=len(head.data.materials)-1
 scalp_faces=neck_faces=0
 for poly in head.data.polygons:
  w=head.matrix_world@poly.center
  if w.y>-0.028 and w.z>1.655:poly.material_index=scalp_i;scalp_faces+=1
  elif w.y>-0.012 and w.z<=1.655:poly.material_index=neck_i;neck_faces+=1
 groom=bpy.data.objects['V333_COMPACT_SCALP_FOLLOWING_CURL_GROOM'];groom.data.bevel_depth=0.00048
 center=Vector((0,-0.064,1.728))
 for spline in groom.data.splines:
  for point in spline.points:
   v=Vector(point.co[:3]);d=v-center;v.x=center.x+d.x*0.84;v.y=center.y+d.y*0.87;v.z=center.z+d.z*0.92
   if v.z<1.755:v.z+=(1.755-v.z)*0.62
   point.co=(*v,1)
 groom.name='V334_COMPACT_REFINED_CURL_GROOM';scene=bpy.context.scene;scene['V334_STATUS']='GROOM_AND_REAR_PROJECTION_CLEANUP_VISUAL_REVIEW_REQUIRED'
 cam=bpy.data.objects['V323_CAMERA'];target=Vector((0,-0.065,1.675));renders={
  'front':render(scene,cam,RENDERS/'v334_front.png',Vector((0,-1.28,1.69)),target,104),
  'three_quarter':render(scene,cam,RENDERS/'v334_three_quarter.png',Vector((0.58,-1.16,1.71)),target,100),
  'profile':render(scene,cam,RENDERS/'v334_profile.png',Vector((1.22,-0.03,1.68)),target,100),
  'rear_three_quarter':render(scene,cam,RENDERS/'v334_rear_three_quarter.png',Vector((0.75,0.92,1.72)),Vector((0,0,1.71)),96)}
 bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT),check_existing=False)
 rec={'schema':'v334-groom-projection-cleanup-v1','status':'BUILT_VISUAL_REVIEW_REQUIRED','source':{'path':str(SOURCE.relative_to(ROOT)),'sha256':sha(SOURCE)},'rear_scalp_faces':scalp_faces,'rear_neck_faces':neck_faces,'renders':renders,'output':{'path':str(OUTPUT.relative_to(ROOT)),'sha256':sha(OUTPUT)}};AUDIT.write_text(json.dumps(rec,indent=2,sort_keys=True)+'\n');print('V334_GROOM_CLEANUP_OK='+json.dumps(rec['output'],sort_keys=True))
if __name__=='__main__':main()
