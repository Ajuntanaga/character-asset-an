"""Replace V338's rejected blade-like body with a reference-landmark silhouette."""
from pathlib import Path
import hashlib,json
import bpy
from mathutils import Vector
ROOT=Path('/home/ajuntanaga/Projects/Blender/Character Asset_An');SOURCE=ROOT/'production_v338_graphite_guitar_integration'/'Character_An_graphite_guitar_v338.blend';STAGE=ROOT/'production_v339_reference_body_silhouette';OUTPUT=STAGE/'Character_An_reference_body_v339.blend';RENDERS=STAGE/'renders';AUDIT=STAGE/'audit'/'v339_reference_body.json'
# Clockwise outline landmarks traced from strandberg_angle.jpg (1200 square).
PIXELS=[(510,248),(458,246),(395,225),(335,180),(285,92),(260,25),(235,82),(224,170),(233,265),(275,355),(315,430),(330,515),(305,605),(250,685),(195,770),(166,860),(172,955),(220,1050),(292,1125),(372,1165),(430,1148),(462,1108),(474,1060),(468,1028),(525,1020),(695,1013),(742,1028),(772,1075),(805,1032),(842,975),(900,930),(970,895),(1050,860),(1014,812),(958,760),(912,700),(892,628),(894,555),(916,478),(952,408),(971,347),(936,365),(890,392),(832,414),(770,420),(725,405),(700,378),(700,348),(650,330),(590,318),(548,292)]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def outline():
 # Calibrated to the official 330 mm body width and the existing 0.345-0.850 m body station.
 return [(0.345+(v-25)/(1165-25)*0.505,(600-u)/(1050-166)*0.330) for u,v in PIXELS]
def body_mesh(name,pts,z0,z1):
 n=len(pts);verts=[(x,y,z0) for x,y in pts]+[(x,y,z1) for x,y in pts];faces=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]
 for i in range(n):j=(i+1)%n;faces.append((i,j,n+j,n+i))
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update();return mesh
def reveal_mesh(name,pts,z):
 center=Vector((sum(x for x,y in pts)/len(pts),sum(y for x,y in pts)/len(pts),0));inset=[]
 for x,y in pts:inset.append((center.x+(x-center.x)*.982,center.y+(y-center.y)*.982,z))
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(inset,[],[tuple(range(len(inset)))]);mesh.update();return mesh
def aim(o,t):o.rotation_euler=(t-o.location).to_track_quat('-Z','Y').to_euler()
def render(s,c,p,l,t,lens,res):c.location=l;c.data.lens=lens;aim(c,t);s.camera=c;s.render.resolution_x,s.render.resolution_y=res;s.render.resolution_percentage=100;s.render.filepath=str(p);bpy.ops.render.render(write_still=True);return {'path':str(p.relative_to(ROOT)),'sha256':sha(p)}
def main():
 bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
 for p in (STAGE,RENDERS,AUDIT.parent):p.mkdir(parents=True,exist_ok=True)
 pts=outline();body=bpy.data.objects['V206_BODY_CORE'];old=body.data;body.data=body_mesh('V339_REFERENCE_BODY_MESH',pts,-.039,.003);bpy.data.meshes.remove(old)
 for m in list(body.modifiers):body.modifiers.remove(m)
 bevel=body.modifiers.new('V339_BODY_EDGE_RADIUS','BEVEL');bevel.width=.008;bevel.segments=4
 weighted=body.modifiers.new('V339_WEIGHTED_NORMAL','WEIGHTED_NORMAL');weighted.keep_sharp=True
 reveal=bpy.data.objects['V318_BODY_REVEAL'];old=reveal.data;reveal.data=reveal_mesh('V339_REFERENCE_TOP_REVEAL',pts,.004);bpy.data.meshes.remove(old)
 for m in list(reveal.modifiers):reveal.modifiers.remove(m)
 bevel2=reveal.modifiers.new('V339_REVEAL_EDGE','BEVEL');bevel2.width=.0035;bevel2.segments=3
 scene=bpy.context.scene;scene['V339_STATUS']='REFERENCE_BODY_SILHOUETTE_VISUAL_REVIEW_REQUIRED';cam=bpy.data.objects['V323_CAMERA'];renders={'full_front':render(scene,cam,RENDERS/'v339_full_front.png',Vector((.18,-3.75,1.10)),Vector((.10,-.10,1.08)),67,(1000,1200)),'guitar_beauty':render(scene,cam,RENDERS/'v339_guitar_beauty.png',Vector((1.25,-2.25,1.42)),Vector((.33,-.30,1.35)),82,(1100,900)),'guitar_front':render(scene,cam,RENDERS/'v339_guitar_front.png',Vector((.68,-2.25,1.46)),Vector((.34,-.30,1.34)),96,(900,1000))}
 bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT),check_existing=False);rec={'schema':'v339-reference-body-silhouette-v1','status':'BUILT_VISUAL_REVIEW_REQUIRED','source':{'path':str(SOURCE.relative_to(ROOT)),'sha256':sha(SOURCE)},'reference':'references/props/strandberg/strandberg_angle.jpg','landmark_count':len(PIXELS),'body_width_m':max(y for x,y in pts)-min(y for x,y in pts),'body_length_m':max(x for x,y in pts)-min(x for x,y in pts),'renders':renders,'output':{'path':str(OUTPUT.relative_to(ROOT)),'sha256':sha(OUTPUT)}};AUDIT.write_text(json.dumps(rec,indent=2,sort_keys=True)+'\n');print('V339_BODY_OK='+json.dumps(rec['output'],sort_keys=True))
if __name__=='__main__':main()
