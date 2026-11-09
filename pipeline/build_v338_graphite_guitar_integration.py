"""Integrate the complete official-scale V318 guitar into the V334 character."""
from pathlib import Path
import hashlib,json
import bpy
from mathutils import Vector
ROOT=Path('/home/ajuntanaga/Projects/Blender/Character Asset_An');SOURCE=ROOT/'production_v334_groom_projection_cleanup'/'Character_An_groom_projection_cleanup_v334.blend';GUITAR=ROOT/'production_v318_reference_guitar_rebuild'/'Character_An_reference_guitar_rebuild_v318.blend';STAGE=ROOT/'production_v338_graphite_guitar_integration';OUTPUT=STAGE/'Character_An_graphite_guitar_v338.blend';RENDERS=STAGE/'renders';AUDIT=STAGE/'audit'/'v338_graphite_guitar.json'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def material(name,color,rough=.5,metal=0.0,noise=False):
 m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
 if 'Specular IOR Level' in p.inputs:p.inputs['Specular IOR Level'].default_value=.32
 if noise:
  tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=48;tex.inputs['Detail'].default_value=5;tex.inputs['Roughness'].default_value=.64;bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.07;bump.inputs['Distance'].default_value=.0007;l.new(tex.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs['Normal'],p.inputs['Normal'])
 return m
def descendants(names):
 with bpy.data.libraries.load(str(GUITAR),link=False) as (src,dst):dst.objects=[n for n in names if n in src.objects]
 for o in dst.objects:
  if o and o.name not in bpy.context.scene.collection.objects:bpy.context.scene.collection.objects.link(o)
 return [o for o in dst.objects if o]
def assign(o,m):
 if not hasattr(o.data,'materials'):return
 o.data.materials.clear();o.data.materials.append(m)
def aim(o,t):o.rotation_euler=(t-o.location).to_track_quat('-Z','Y').to_euler()
def render(s,c,p,l,t,lens,res):c.location=l;c.data.lens=lens;aim(c,t);s.camera=c;s.render.resolution_x,s.render.resolution_y=res;s.render.resolution_percentage=100;s.render.filepath=str(p);bpy.ops.render.render(write_still=True);return {'path':str(p.relative_to(ROOT)),'sha256':sha(p)}
def main():
 bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
 for p in (STAGE,RENDERS,AUDIT.parent):p.mkdir(parents=True,exist_ok=True)
 with bpy.data.libraries.load(str(GUITAR),link=False) as (src,dst):names=[n for n in src.objects if n=='V206_GUITAR_ROOT' or n.startswith('V206_') or n=='V318_BODY_REVEAL'];dst.objects=names
 imported=[]
 for o in dst.objects:
  if o:bpy.context.scene.collection.objects.link(o);imported.append(o)
 mats={'body':material('V338_GRAPHITE_SATIN',(.035,.045,.055),.38,.18,True),'reveal':material('V338_GRAPHITE_EDGE',(.012,.017,.022),.46,.10,True),'neck':material('V338_DARK_NECK',(.018,.013,.010),.46,0,True),'board':material('V338_EBONY_BOARD',(.004,.003,.0025),.52,0,True),'black':material('V338_BLACK_HARDWARE',(.002,.0025,.003),.28,.48),'steel':material('V338_STEEL_STRINGS',(.24,.27,.30),.21,.86),'marker':material('V338_INLAY',(.36,.38,.40),.30,.25)}
 for o in imported:
  n=o.name
  if n=='V206_BODY_CORE':assign(o,mats['body'])
  elif n=='V318_BODY_REVEAL' or 'REAR_ELECTRONICS_COVER' in n:assign(o,mats['reveal'])
  elif n=='V206_NECK':assign(o,mats['neck'])
  elif n=='V206_FRETBOARD':assign(o,mats['board'])
  elif 'STRING_' in n or n=='V206_FRETS' or 'SCREW' in n:assign(o,mats['steel'])
  elif 'INLAY_' in n:assign(o,mats['marker'])
  elif n.startswith('V206_') and o.type in {'MESH','CURVE'}:assign(o,mats['black'])
 root=bpy.data.objects['V206_GUITAR_ROOT'];scene=bpy.context.scene;scene['V338_STATUS']='GRAPHITE_GUITAR_INTEGRATED_VISUAL_REVIEW_REQUIRED';scene['V338_GUITAR_OBJECT_COUNT']=len(imported)
 cam=bpy.data.objects['V323_CAMERA'];renders={'full_front':render(scene,cam,RENDERS/'v338_full_front.png',Vector((.18,-3.75,1.10)),Vector((.10,-.10,1.08)),67,(1000,1200)),'full_three_quarter':render(scene,cam,RENDERS/'v338_full_three_quarter.png',Vector((1.45,-3.25,1.18)),Vector((.12,-.12,1.10)),64,(1000,1200)),'guitar_beauty':render(scene,cam,RENDERS/'v338_guitar_beauty.png',Vector((1.25,-2.25,1.42)),Vector((.33,-.30,1.35)),82,(1100,900))}
 bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT),check_existing=False);rec={'schema':'v338-graphite-guitar-integration-v1','status':'BUILT_VISUAL_REVIEW_REQUIRED','source':{'path':str(SOURCE.relative_to(ROOT)),'sha256':sha(SOURCE)},'guitar_source':{'path':str(GUITAR.relative_to(ROOT)),'sha256':sha(GUITAR)},'imported_object_count':len(imported),'root_transform':{'location':list(root.location),'rotation_euler':list(root.rotation_euler),'scale':list(root.scale)},'renders':renders,'output':{'path':str(OUTPUT.relative_to(ROOT)),'sha256':sha(OUTPUT)}};AUDIT.write_text(json.dumps(rec,indent=2,sort_keys=True)+'\n');print('V338_GUITAR_OK='+json.dumps(rec['output'],sort_keys=True))
if __name__=='__main__':main()
