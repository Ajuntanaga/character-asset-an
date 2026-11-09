"""Build a non-self-intersecting guitar body from the extracted product contour."""
from pathlib import Path
import hashlib,json
import bpy
from mathutils import Vector
ROOT=Path('/home/ajuntanaga/Projects/Blender/Character Asset_An');SOURCE=ROOT/'production_v338_graphite_guitar_integration'/'Character_An_graphite_guitar_v338.blend';CONTOUR=ROOT/'production_v340_image_contour_body'/'analysis'/'strandberg_product_contour.json';STAGE=ROOT/'production_v340_image_contour_body';OUTPUT=STAGE/'Character_An_image_contour_guitar_v340.blend';RENDERS=STAGE/'renders';AUDIT=STAGE/'audit'/'v340_image_contour_guitar.json'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def load_points():
 data=json.loads(CONTOUR.read_text());w,h=data['image_size'];raw=data['points_px'];filtered=[(u,v) for u,v in raw if not (w*.34<u<w*.59 and v<h*.36)]
 min_u,max_u=min(u for u,v in filtered),max(u for u,v in filtered);min_v,max_v=min(v for u,v in filtered),max(v for u,v in filtered)
 points=[(.345+(v-min_v)/(max_v-min_v)*.505,(max_u+min_u-2*u)/(max_u-min_u)*.165) for u,v in filtered]
 return points,raw,filtered
def mesh(name,pts,z0,z1):
 n=len(pts);verts=[(x,y,z0) for x,y in pts]+[(x,y,z1) for x,y in pts];faces=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,n+(i+1)%n,n+i) for i in range(n)];m=bpy.data.meshes.new(name);m.from_pydata(verts,[],faces);m.update();return m
def aim(o,t):o.rotation_euler=(Vector(t)-o.location).to_track_quat('-Z','Y').to_euler()
def render(s,c,p,l,t,lens,res):c.location=l;c.data.lens=lens;aim(c,t);s.camera=c;s.render.resolution_x,s.render.resolution_y=res;s.render.resolution_percentage=100;s.render.filepath=str(p);bpy.ops.render.render(write_still=True);return {'path':str(p.relative_to(ROOT)),'sha256':sha(p)}
def main():
 bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
 for p in (STAGE,RENDERS,AUDIT.parent):p.mkdir(parents=True,exist_ok=True)
 pts,raw,filtered=load_points();body=bpy.data.objects['V206_BODY_CORE'];old=body.data;body.data=mesh('V340_IMAGE_CONTOUR_BODY',pts,-.039,.003);bpy.data.meshes.remove(old)
 for mod in list(body.modifiers):body.modifiers.remove(mod)
 bevel=body.modifiers.new('V340_BODY_EDGE_RADIUS','BEVEL');bevel.width=.0075;bevel.segments=5
 body.modifiers.new('V340_WEIGHTED_NORMAL','WEIGHTED_NORMAL')
 reveal=bpy.data.objects.get('V318_BODY_REVEAL')
 if reveal:reveal.hide_render=True;reveal.hide_viewport=True
 scene=bpy.context.scene;scene['V340_STATUS']='IMAGE_CONTOUR_GUITAR_VISUAL_REVIEW_REQUIRED';cam=bpy.data.objects['V323_CAMERA'];renders={'full_front':render(scene,cam,RENDERS/'v340_full_front.png',(.18,-3.75,1.10),(.10,-.10,1.08),67,(1000,1200)),'guitar_beauty':render(scene,cam,RENDERS/'v340_guitar_beauty.png',(1.25,-2.25,1.42),(.33,-.30,1.35),82,(1100,900)),'guitar_front':render(scene,cam,RENDERS/'v340_guitar_front.png',(.68,-2.25,1.46),(.34,-.30,1.34),96,(900,1000))}
 bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT),check_existing=False);rec={'schema':'v340-image-contour-guitar-v1','status':'BUILT_VISUAL_REVIEW_REQUIRED','source':{'path':str(SOURCE.relative_to(ROOT)),'sha256':sha(SOURCE)},'contour':{'path':str(CONTOUR.relative_to(ROOT)),'sha256':sha(CONTOUR),'raw_points':len(raw),'filtered_points':len(filtered)},'body_width_m':max(y for x,y in pts)-min(y for x,y in pts),'body_length_m':max(x for x,y in pts)-min(x for x,y in pts),'renders':renders,'output':{'path':str(OUTPUT.relative_to(ROOT)),'sha256':sha(OUTPUT)}};AUDIT.parent.mkdir(parents=True,exist_ok=True);AUDIT.write_text(json.dumps(rec,indent=2,sort_keys=True)+'\n');print('V340_CONTOUR_GUITAR_OK='+json.dumps(rec['output'],sort_keys=True))
if __name__=='__main__':main()
