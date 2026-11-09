"""Remove the obsolete figured-top overlay obscuring the V340 contour body."""
from pathlib import Path
import hashlib,json
import bpy
from mathutils import Vector
ROOT=Path('/home/ajuntanaga/Projects/Blender/Character Asset_An');SOURCE=ROOT/'production_v340_image_contour_body'/'Character_An_image_contour_guitar_v340.blend';STAGE=ROOT/'production_v341_clean_contour_guitar';OUTPUT=STAGE/'Character_An_clean_contour_guitar_v341.blend';RENDERS=STAGE/'renders';AUDIT=STAGE/'audit'/'v341_clean_contour_guitar.json'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def aim(o,t):o.rotation_euler=(Vector(t)-o.location).to_track_quat('-Z','Y').to_euler()
def render(s,c,p,l,t,lens,res):c.location=l;c.data.lens=lens;aim(c,t);s.camera=c;s.render.resolution_x,s.render.resolution_y=res;s.render.resolution_percentage=100;s.render.filepath=str(p);bpy.ops.render.render(write_still=True);return {'path':str(p.relative_to(ROOT)),'sha256':sha(p)}
def main():
 bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
 for p in (STAGE,RENDERS,AUDIT.parent):p.mkdir(parents=True,exist_ok=True)
 removed=[]
 for name in ('V206_FIGURED_TOP','V318_BODY_REVEAL'):
  o=bpy.data.objects.get(name)
  if o:removed.append(name);bpy.data.objects.remove(o,do_unlink=True)
 s=bpy.context.scene;s['V341_STATUS']='CLEAN_CONTOUR_GUITAR_VISUAL_REVIEW_REQUIRED';c=bpy.data.objects['V323_CAMERA'];renders={'full_front':render(s,c,RENDERS/'v341_full_front.png',(.18,-3.75,1.10),(.10,-.10,1.08),67,(1000,1200)),'guitar_beauty':render(s,c,RENDERS/'v341_guitar_beauty.png',(1.25,-2.25,1.42),(.33,-.30,1.35),82,(1100,900)),'guitar_front':render(s,c,RENDERS/'v341_guitar_front.png',(.68,-2.25,1.46),(.34,-.30,1.34),96,(900,1000))}
 bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT),check_existing=False);rec={'schema':'v341-clean-contour-guitar-v1','status':'BUILT_VISUAL_REVIEW_REQUIRED','source':{'path':str(SOURCE.relative_to(ROOT)),'sha256':sha(SOURCE)},'removed_legacy_overlays':removed,'renders':renders,'output':{'path':str(OUTPUT.relative_to(ROOT)),'sha256':sha(OUTPUT)}};AUDIT.write_text(json.dumps(rec,indent=2,sort_keys=True)+'\n');print('V341_CLEAN_GUITAR_OK='+json.dumps(rec['output'],sort_keys=True))
if __name__=='__main__':main()
