"""Render unobstructed neutral wardrobe inspection while preserving performance state."""

from pathlib import Path
import hashlib,json,bpy
from mathutils import Vector

ROOT=Path("/home/ajuntanaga/Projects/Blender/Character Asset_An");SOURCE=ROOT/"production_v264_waist_cleanup"/"Character_An_waist_cleanup_v264.blend";STAGE=ROOT/"production_v265_neutral_wardrobe_inspection";OUTPUT=STAGE/"Character_An_neutral_wardrobe_inspection_v265.blend";RENDERS=STAGE/"renders";AUDIT=STAGE/"audit"
def sha(p):
 h=hashlib.sha256();
 with Path(p).open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()
def point_at(o,t):o.rotation_euler=(t-o.location).to_track_quat("-Z","Y").to_euler()
def main():
 if Path(bpy.data.filepath).resolve()!=SOURCE.resolve():raise RuntimeError(f"Open V264 first: {SOURCE}")
 STAGE.mkdir(parents=True,exist_ok=True);RENDERS.mkdir(parents=True,exist_ok=True);AUDIT.mkdir(parents=True,exist_ok=True)
 main_rig=bpy.data.objects["V239_CLEAN_CHARACTER_RIG"];hand_rig=bpy.data.objects["V250_FRETTING_HAND_RIG"]
 old_main=main_rig.data.pose_position;old_hand=hand_rig.data.pose_position;guitar=[o for o in bpy.context.scene.objects if o.name.startswith("V206_")];hidden={o.name:(o.hide_render,o.hide_viewport) for o in guitar}
 main_rig.data.pose_position="REST";hand_rig.data.pose_position="REST"
 for o in guitar:o.hide_render=True;o.hide_viewport=True
 bpy.context.view_layer.update()
 scene=bpy.context.scene;scene.render.engine="BLENDER_EEVEE";scene.render.image_settings.file_format="PNG";scene.view_settings.look="AgX - Medium High Contrast";cam=bpy.data.objects["CAM_V211_FRONT"]
 views={"front":(Vector((0,-3.5,1)),Vector((0,0,1)),70,(900,1000)),"three_quarter":(Vector((-2.45,-2.65,1.1)),Vector((0,0,1)),72,(900,1000)),"profile":(Vector((-3.4,0,1.05)),Vector((0,0,1)),72,(900,1000)),"upper_front":(Vector((0,-2.1,1.28)),Vector((0,0,1.25)),78,(1000,1000))};renders={}
 for label,(loc,target,lens,res) in views.items():
  cam.location=loc;cam.data.lens=lens;point_at(cam,target);scene.camera=cam;scene.render.resolution_x,scene.render.resolution_y=res;scene.render.resolution_percentage=100;p=RENDERS/f"v265_neutral_{label}.png";scene.render.filepath=str(p);bpy.ops.render.render(write_still=True);renders[label]={"path":str(p.relative_to(ROOT)),"sha256":sha(p)}
 main_rig.data.pose_position=old_main;hand_rig.data.pose_position=old_hand
 for o in guitar:o.hide_render,o.hide_viewport=hidden[o.name]
 bpy.context.view_layer.update()
 rec={"schema":"v265-neutral-wardrobe-inspection-v1","status":"RENDERED_NEUTRAL_INSPECTION","source":{"path":str(SOURCE.relative_to(ROOT)),"sha256":sha(SOURCE)},"renders":renders,"guitar_objects_temporarily_hidden":len(guitar),"output":{"path":str(OUTPUT.relative_to(ROOT))}}
 scene["V265_STATUS"]="NEUTRAL_WARDROBE_INSPECTION_RENDERED";bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT),check_existing=False);rec["output"]["sha256"]=sha(OUTPUT);(AUDIT/"v265_neutral_wardrobe_inspection.json").write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n");print("V265_NEUTRAL_WARDROBE_OK="+json.dumps(rec,sort_keys=True))
if __name__=="__main__":main()
