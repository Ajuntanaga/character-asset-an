"""Promote the deformable jacket shell without V325's rejected flat panels."""
from pathlib import Path
import hashlib,json
import bpy
from mathutils import Vector
ROOT=Path('/home/ajuntanaga/Projects/Blender/Character Asset_An');SOURCE=ROOT/'production_v334_groom_projection_cleanup'/'Character_An_groom_projection_cleanup_v334.blend';WARDROBE=ROOT/'production_v325_wardrobe_foundation'/'Character_An_wardrobe_foundation_v325.blend';STAGE=ROOT/'production_v337_tailored_jacket_shell';OUTPUT=STAGE/'Character_An_tailored_jacket_shell_v337.blend';RENDERS=STAGE/'renders';AUDIT=STAGE/'audit'/'v337_tailored_jacket_shell.json'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def material():
 m=bpy.data.materials.new('V337_BLACK_WASHED_DENIM');m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF');p.inputs['Base Color'].default_value=(.0022,.0028,.0038,1);p.inputs['Roughness'].default_value=.62;p.inputs['Metallic'].default_value=0
 noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=155;noise.inputs['Detail'].default_value=2.4;noise.inputs['Roughness'].default_value=.72;bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.16;bump.inputs['Distance'].default_value=.0015;l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs['Normal'],p.inputs['Normal']);return m
def append_jacket():
 with bpy.data.libraries.load(str(WARDROBE),link=False) as (src,dst):dst.objects=['V325_WORK_JACKET']
 o=dst.objects[0];bpy.context.scene.collection.objects.link(o);o.name='V337_TAILORED_WORK_JACKET';return o
def aim(o,t):o.rotation_euler=(t-o.location).to_track_quat('-Z','Y').to_euler()
def render(s,c,p,l,t,lens,res):c.location=l;c.data.lens=lens;aim(c,t);s.camera=c;s.render.resolution_x,s.render.resolution_y=res;s.render.resolution_percentage=100;s.render.filepath=str(p);bpy.ops.render.render(write_still=True);return {'path':str(p.relative_to(ROOT)),'sha256':sha(p)}
def main():
 bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
 for p in (STAGE,RENDERS,AUDIT.parent):p.mkdir(parents=True,exist_ok=True)
 jacket=append_jacket();rig=bpy.data.objects['V322_MB_MALE_RIG']
 for mod in jacket.modifiers:
  if mod.type=='ARMATURE':mod.object=rig
 jacket.data.materials.clear();jacket.data.materials.append(material())
 solid=next((m for m in jacket.modifiers if m.type=='SOLIDIFY'),None)
 if solid:solid.thickness=.0032;solid.offset=.15
 bevel=jacket.modifiers.new('V337_SOFT_GARMENT_EDGES','BEVEL');bevel.width=.0018;bevel.segments=2
 sub=next((m for m in jacket.modifiers if m.type=='SUBSURF'),None)
 if sub:sub.levels=1;sub.render_levels=2
 scene=bpy.context.scene;scene['V337_STATUS']='TAILORED_JACKET_SHELL_VISUAL_REVIEW_REQUIRED';cam=bpy.data.objects['V323_CAMERA'];renders={
  'torso_front':render(scene,cam,RENDERS/'v337_torso_front.png',Vector((0,-2.05,1.35)),Vector((0,-.03,1.35)),78,(900,1000)),
  'torso_three_quarter':render(scene,cam,RENDERS/'v337_torso_three_quarter.png',Vector((1.0,-1.82,1.38)),Vector((0,-.02,1.34)),76,(900,1000)),
  'full_front':render(scene,cam,RENDERS/'v337_full_front.png',Vector((0,-3.55,1.02)),Vector((0,0,1.0)),68,(900,1100))}
 bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT),check_existing=False);rec={'schema':'v337-tailored-jacket-shell-v1','status':'BUILT_VISUAL_REVIEW_REQUIRED','source':{'path':str(SOURCE.relative_to(ROOT)),'sha256':sha(SOURCE)},'wardrobe_source':{'path':str(WARDROBE.relative_to(ROOT)),'sha256':sha(WARDROBE)},'jacket':jacket.name,'vertices':len(jacket.data.vertices),'polygons':len(jacket.data.polygons),'renders':renders,'output':{'path':str(OUTPUT.relative_to(ROOT)),'sha256':sha(OUTPUT)}};AUDIT.write_text(json.dumps(rec,indent=2,sort_keys=True)+'\n');print('V337_JACKET_OK='+json.dumps(rec['output'],sort_keys=True))
if __name__=='__main__':main()
