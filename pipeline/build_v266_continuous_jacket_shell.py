"""Rebuild the jacket as a continuous wrist-height shell with tapered shoulders."""

from pathlib import Path
import hashlib,json,bmesh,bpy
from mathutils import Vector

ROOT=Path("/home/ajuntanaga/Projects/Blender/Character Asset_An");SOURCE=ROOT/"production_v265_neutral_wardrobe_inspection"/"Character_An_neutral_wardrobe_inspection_v265.blend";STAGE=ROOT/"production_v266_continuous_jacket_shell";OUTPUT=STAGE/"Character_An_continuous_jacket_v266.blend";RENDERS=STAGE/"renders";AUDIT=STAGE/"audit"
UPPER_Z=1.47
EXCLUDE_HANDS=False
HAND_WEIGHT_LIMIT=.65
def sha(p):
 h=hashlib.sha256();
 with Path(p).open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()
def point_at(o,t):o.rotation_euler=(t-o.location).to_track_quat("-Z","Y").to_euler()
def main():
 if Path(bpy.data.filepath).resolve()!=SOURCE.resolve():raise RuntimeError(f"Open V265 first: {SOURCE}")
 STAGE.mkdir(parents=True,exist_ok=True);RENDERS.mkdir(parents=True,exist_ok=True);AUDIT.mkdir(parents=True,exist_ok=True)
 for name in ("V262_LONG_SLEEVE_OPEN_JACKET","V263_BREAST_POCKET_L","V263_BREAST_POCKET_R","V263_POCKET_FLAP_L","V263_POCKET_FLAP_R","V263_HEM_STITCH"):
  o=bpy.data.objects.get(name)
  if o:o.hide_viewport=True;o.hide_render=True
 body=bpy.data.objects["V211_BODY_NEUTRAL"];rig=bpy.data.objects["V239_CLEAN_CHARACTER_RIG"];coll=bpy.data.collections.get("V266_CONTINUOUS_JACKET") or bpy.data.collections.new("V266_CONTINUOUS_JACKET")
 if coll.name not in bpy.context.scene.collection.children:bpy.context.scene.collection.children.link(coll)
 jacket=body.copy();jacket.data=body.data.copy();jacket.name="V266_CONTINUOUS_OPEN_JACKET";coll.objects.link(jacket)
 for mod in tuple(jacket.modifiers):jacket.modifiers.remove(mod)
 names={g.index:g.name.lower() for g in jacket.vertex_groups};bm=bmesh.new();bm.from_mesh(jacket.data);mw=jacket.matrix_world;delete=[]
 for v in bm.verts:
  p=mw@v.co;groups={names.get(g.group,""):g.weight for g in jacket.data.vertices[v.index].groups};hand=max((w for name,w in groups.items() if any(t in name for t in ("hand","thumb","f_index","f_middle","f_ring","f_pinky"))),default=0.0)
  keep=.70<=p.z<=UPPER_Z and not (p.z>1.47 and abs(p.x)<.14);opening=p.y<-.035 and abs(p.x)<(.068+max(0,p.z-.94)*.105)
  if EXCLUDE_HANDS and hand>HAND_WEIGHT_LIMIT:keep=False
  if not keep or opening:delete.append(v);continue
  # Blend shoulder width inward above the upper chest without narrowing cuffs.
  shoulder=max(0,min(1,(p.z-1.23)/.20))*max(0,min(1,(abs(p.x)-.14)/.18))
  if shoulder>0:v.co.x*=1-.065*shoulder;v.co.y*=1-.025*shoulder
 bmesh.ops.delete(bm,geom=delete,context="VERTS");bm.to_mesh(jacket.data);bm.free();jacket.data.update();jacket.data.materials.clear();jacket.data.materials.append(bpy.data.materials["MAT_V262_WASHED_CHARCOAL_DENIM"])
 sub=jacket.modifiers.new("V266_SUBDIVISION","SUBSURF");sub.levels=1;sub.render_levels=2;disp=jacket.modifiers.new("V266_CLEARANCE","DISPLACE");disp.mid_level=.5;disp.strength=.008;solid=jacket.modifiers.new("V266_THICKNESS","SOLIDIFY");solid.thickness=.004;solid.offset=.1;smooth=jacket.modifiers.new("V266_RELAX","SMOOTH");smooth.factor=.1;smooth.iterations=2;arm=jacket.modifiers.new("V266_RIG","ARMATURE");arm.object=rig;arm.use_deform_preserve_volume=True
 for p in jacket.data.polygons:p.use_smooth=True
 scene=bpy.context.scene;scene.render.engine="BLENDER_EEVEE";scene.render.image_settings.file_format="PNG";scene.view_settings.look="AgX - Medium High Contrast";cam=bpy.data.objects["CAM_V211_FRONT"];renders={}
 # Neutral inspection.
 main_rig=rig;hand_rig=bpy.data.objects["V250_FRETTING_HAND_RIG"];om=main_rig.data.pose_position;oh=hand_rig.data.pose_position;guitar=[o for o in scene.objects if o.name.startswith("V206_")];hidden={o.name:(o.hide_render,o.hide_viewport) for o in guitar};main_rig.data.pose_position="REST";hand_rig.data.pose_position="REST"
 for o in guitar:o.hide_render=True;o.hide_viewport=True
 bpy.context.view_layer.update()
 for label,loc,target,lens in (("neutral_front",Vector((0,-3.5,1)),Vector((0,0,1)),70),("neutral_three_quarter",Vector((-2.45,-2.65,1.1)),Vector((0,0,1)),72),("neutral_upper",Vector((0,-2.1,1.28)),Vector((0,0,1.25)),78)):
  cam.location=loc;cam.data.lens=lens;point_at(cam,target);scene.camera=cam;scene.render.resolution_x=900 if label!="neutral_upper" else 1000;scene.render.resolution_y=1000;scene.render.resolution_percentage=100;p=RENDERS/f"v266_{label}.png";scene.render.filepath=str(p);bpy.ops.render.render(write_still=True);renders[label]={"path":str(p.relative_to(ROOT)),"sha256":sha(p)}
 main_rig.data.pose_position=om;hand_rig.data.pose_position=oh
 for o in guitar:o.hide_render,o.hide_viewport=hidden[o.name]
 bpy.context.view_layer.update();cam.location=Vector((0,-3.75,1));cam.data.lens=66;point_at(cam,Vector((0,0,1)));scene.camera=cam;scene.render.resolution_x=900;scene.render.resolution_y=1000;p=RENDERS/"v266_performance_front.png";scene.render.filepath=str(p);bpy.ops.render.render(write_still=True);renders["performance_front"]={"path":str(p.relative_to(ROOT)),"sha256":sha(p)}
 rec={"schema":"v266-continuous-jacket-shell-v1","status":"BUILT_VISUAL_REVIEW_REQUIRED","source":{"path":str(SOURCE.relative_to(ROOT)),"sha256":sha(SOURCE)},"jacket":{"vertices":len(jacket.data.vertices),"polygons":len(jacket.data.polygons)},"renders":renders,"output":{"path":str(OUTPUT.relative_to(ROOT))}}
 scene["V266_STATUS"]="CONTINUOUS_TAPERED_JACKET_VISUAL_REVIEW_REQUIRED";bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT),check_existing=False);rec["output"]["sha256"]=sha(OUTPUT);(AUDIT/"v266_continuous_jacket.json").write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n");print("V266_CONTINUOUS_JACKET_OK="+json.dumps(rec,sort_keys=True))
if __name__=="__main__":main()
