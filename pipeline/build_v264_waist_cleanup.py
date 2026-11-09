"""Remove the toroidal trouser waistband artifact and tune trouser response."""

from pathlib import Path
import hashlib,json,bpy
from mathutils import Vector

ROOT=Path("/home/ajuntanaga/Projects/Blender/Character Asset_An"); SOURCE=ROOT/"production_v263_tailoring_details"/"Character_An_tailoring_details_v263.blend"; STAGE=ROOT/"production_v264_waist_cleanup"; OUTPUT=STAGE/"Character_An_waist_cleanup_v264.blend"; RENDERS=STAGE/"renders"; AUDIT=STAGE/"audit"
def sha(p):
 h=hashlib.sha256();
 with Path(p).open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()
def point_at(o,t):o.rotation_euler=(t-o.location).to_track_quat("-Z","Y").to_euler()
def main():
 if Path(bpy.data.filepath).resolve()!=SOURCE.resolve():raise RuntimeError(f"Open V263 first: {SOURCE}")
 STAGE.mkdir(parents=True,exist_ok=True);RENDERS.mkdir(parents=True,exist_ok=True);AUDIT.mkdir(parents=True,exist_ok=True)
 waist=bpy.data.objects.get("V243_TROUSER_WAISTBAND")
 if waist:waist.hide_viewport=True;waist.hide_render=True
 material=bpy.data.materials.get("MAT_V241_TROUSERS")
 if material and material.use_nodes:
  bs=material.node_tree.nodes.get("Principled BSDF");bs.inputs["Base Color"].default_value=(.012,.011,.012,1);bs.inputs["Roughness"].default_value=.78
  if "Specular IOR Level" in bs.inputs:bs.inputs["Specular IOR Level"].default_value=.18
 scene=bpy.context.scene;scene.render.engine="BLENDER_EEVEE";scene.render.image_settings.file_format="PNG";scene.view_settings.look="AgX - Medium High Contrast";cam=bpy.data.objects["CAM_V211_FRONT"]
 views={"full_front":(Vector((0,-3.75,1)),Vector((0,0,1)),66,(900,1000)),"upper_front":(Vector((0,-2.05,1.28)),Vector((0,0,1.25)),76,(1000,1000)),"upper_three_quarter":(Vector((-1.65,-1.85,1.32)),Vector((0,0,1.22)),82,(1000,1000))};renders={}
 for label,(loc,target,lens,res) in views.items():
  cam.location=loc;cam.data.lens=lens;point_at(cam,target);scene.camera=cam;scene.render.resolution_x,scene.render.resolution_y=res;scene.render.resolution_percentage=100;p=RENDERS/f"v264_{label}.png";scene.render.filepath=str(p);bpy.ops.render.render(write_still=True);renders[label]={"path":str(p.relative_to(ROOT)),"sha256":sha(p)}
 rec={"schema":"v264-waist-cleanup-v1","status":"BUILT_VISUAL_REVIEW_REQUIRED","source":{"path":str(SOURCE.relative_to(ROOT)),"sha256":sha(SOURCE)},"hidden":waist.name if waist else None,"renders":renders,"output":{"path":str(OUTPUT.relative_to(ROOT))}}
 scene["V264_STATUS"]="WAIST_ARTIFACT_REMOVED";bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT),check_existing=False);rec["output"]["sha256"]=sha(OUTPUT);(AUDIT/"v264_waist_cleanup.json").write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n");print("V264_WAIST_CLEANUP_OK="+json.dumps(rec,sort_keys=True))
if __name__=="__main__":main()
