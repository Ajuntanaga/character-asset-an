"""Revert failed overlay eyeballs and add only subtle wet corneal domes."""
from pathlib import Path
import hashlib,json
import bpy
from mathutils import Vector
ROOT=Path('/home/ajuntanaga/Projects/Blender/Character Asset_An');SOURCE=ROOT/'production_v334_groom_projection_cleanup'/'Character_An_groom_projection_cleanup_v334.blend';STAGE=ROOT/'production_v336_cornea_dome_foundation';OUTPUT=STAGE/'Character_An_cornea_dome_foundation_v336.blend';RENDERS=STAGE/'renders';AUDIT=STAGE/'audit'/'v336_cornea_dome_foundation.json'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def parent(o,r,b):w=o.matrix_world.copy();o.parent=r;o.parent_type='BONE';o.parent_bone=b;o.matrix_world=w
def material():
 m=bpy.data.materials.new('V336_WET_CORNEA');m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(1,1,1,1);p.inputs['Roughness'].default_value=.025;p.inputs['Transmission Weight'].default_value=1;p.inputs['IOR'].default_value=1.376;p.inputs['Alpha'].default_value=.10;m.surface_render_method='DITHERED';return m
def aim(o,t):o.rotation_euler=(t-o.location).to_track_quat('-Z','Y').to_euler()
def render(s,c,p,l,t,lens):c.location=l;c.data.lens=lens;aim(c,t);s.camera=c;s.render.resolution_x=s.render.resolution_y=900;s.render.resolution_percentage=100;s.render.filepath=str(p);bpy.ops.render.render(write_still=True);return {'path':str(p.relative_to(ROOT)),'sha256':sha(p)}
def main():
 bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
 for p in (STAGE,RENDERS,AUDIT.parent):p.mkdir(parents=True,exist_ok=True)
 r=bpy.data.objects['V322_MB_MALE_RIG'];m=material();objs=[]
 for label,x,bone in (('L',-.034,'eye.L'),('R',.034,'eye.R')):
  bpy.ops.mesh.primitive_uv_sphere_add(segments=64,ring_count=32,radius=.0072,location=(x,-.1560,1.692));o=bpy.context.object;o.name=f'V336_CORNEA_DOME_{label}';o.scale=(1.0,.42,.72);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m);bpy.ops.object.shade_smooth();parent(o,r,bone);objs.append(o.name)
 s=bpy.context.scene;s['V336_STATUS']='SUBTLE_CORNEA_DOMES_VISUAL_REVIEW_REQUIRED';c=bpy.data.objects['V323_CAMERA'];t=Vector((0,-.065,1.675));renders={'front':render(s,c,RENDERS/'v336_front.png',Vector((0,-1.28,1.69)),t,112),'three_quarter':render(s,c,RENDERS/'v336_three_quarter.png',Vector((.58,-1.16,1.71)),t,106),'closeup':render(s,c,RENDERS/'v336_closeup.png',Vector((0,-.82,1.70)),Vector((0,-.12,1.692)),118)}
 bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT),check_existing=False);rec={'schema':'v336-cornea-dome-foundation-v1','status':'BUILT_VISUAL_REVIEW_REQUIRED','source':{'path':str(SOURCE.relative_to(ROOT)),'sha256':sha(SOURCE)},'objects':objs,'renders':renders,'output':{'path':str(OUTPUT.relative_to(ROOT)),'sha256':sha(OUTPUT)}};AUDIT.write_text(json.dumps(rec,indent=2,sort_keys=True)+'\n');print('V336_CORNEA_OK='+json.dumps(rec['output'],sort_keys=True))
if __name__=='__main__':main()
