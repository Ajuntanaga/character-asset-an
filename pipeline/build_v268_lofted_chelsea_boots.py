"""Replace block boots with lofted Chelsea uppers and reference-profile soles."""

from pathlib import Path
import hashlib,json,math,bpy
from mathutils import Vector

ROOT=Path("/home/ajuntanaga/Projects/Blender/Character Asset_An");SOURCE=ROOT/"production_v265_neutral_wardrobe_inspection"/"Character_An_neutral_wardrobe_inspection_v265.blend";STAGE=ROOT/"production_v268_lofted_chelsea_boots";OUTPUT=STAGE/"Character_An_lofted_chelsea_boots_v268.blend";RENDERS=STAGE/"renders";AUDIT=STAGE/"audit";RIG="V239_CLEAN_CHARACTER_RIG"
def sha(p):
 h=hashlib.sha256();
 with Path(p).open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()
def point_at(o,t):o.rotation_euler=(t-o.location).to_track_quat("-Z","Y").to_euler()
def material(name,color,rough):
 m=bpy.data.materials.get(name) or bpy.data.materials.new(name);m.use_nodes=True;bs=m.node_tree.nodes.get("Principled BSDF");bs.inputs["Base Color"].default_value=color;bs.inputs["Roughness"].default_value=rough
 if "Specular IOR Level" in bs.inputs:bs.inputs["Specular IOR Level"].default_value=.28
 return m
def parent(obj,bone):
 w=obj.matrix_world.copy();obj.parent=bpy.data.objects[RIG];obj.parent_type="BONE";obj.parent_bone=bone;obj.matrix_world=w
def mesh_obj(name,verts,faces,coll,mat,subdiv=1):
 me=bpy.data.meshes.new(name+"_MESH");me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(name,me);coll.objects.link(o);me.materials.append(mat)
 for p in me.polygons:p.use_smooth=True
 if subdiv:
  s=o.modifiers.new(name+"_SUBDIV","SUBSURF");s.levels=subdiv;s.render_levels=2
 b=o.modifiers.new(name+"_EDGE_SOFTEN","BEVEL");b.width=.003;b.segments=3
 return o
def loft_foot(name,x,coll,mat):
 sections=[(-.195,.070,.040,.070),(-.155,.088,.055,.078),(-.085,.088,.067,.086),(-.010,.080,.074,.094),(.065,.071,.070,.105),(.115,.066,.055,.112)];seg=16;verts=[]
 for y,w,h,zc in sections:
  for i in range(seg):
   a=2*math.pi*i/seg;verts.append((x+w*math.cos(a),y,zc+h*math.sin(a)))
 faces=[]
 for r in range(len(sections)-1):
  for i in range(seg):j=(i+1)%seg;faces.append((r*seg+i,r*seg+j,(r+1)*seg+j,(r+1)*seg+i))
 faces.append(tuple(range(seg-1,-1,-1)));faces.append(tuple((len(sections)-1)*seg+i for i in range(seg)))
 return mesh_obj(name,verts,faces,coll,mat,1)
def loft_shaft(name,x,coll,mat):
 rings=[(.105,.071,.068),(.165,.073,.069),(.235,.075,.071),(.305,.077,.073)];seg=20;verts=[]
 for z,rx,ry in rings:
  for i in range(seg):a=2*math.pi*i/seg;verts.append((x+rx*math.cos(a),.028+ry*math.sin(a),z))
 faces=[]
 for r in range(len(rings)-1):
  for i in range(seg):j=(i+1)%seg;faces.append((r*seg+i,r*seg+j,(r+1)*seg+j,(r+1)*seg+i))
 return mesh_obj(name,verts,faces,coll,mat,1)
def rounded(name,loc,scale,coll,mat,bevel):
 bpy.ops.mesh.primitive_cube_add(location=loc);o=bpy.context.object;o.name=name
 for c in tuple(o.users_collection):c.objects.unlink(o)
 coll.objects.link(o);o.scale=(scale[0]/2,scale[1]/2,scale[2]/2);bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(mat);b=o.modifiers.new(name+"_BEVEL","BEVEL");b.width=bevel;b.segments=5
 for p in o.data.polygons:p.use_smooth=True
 return o
def main():
 if Path(bpy.data.filepath).resolve()!=SOURCE.resolve():raise RuntimeError(f"Open V265 first: {SOURCE}")
 STAGE.mkdir(parents=True,exist_ok=True);RENDERS.mkdir(parents=True,exist_ok=True);AUDIT.mkdir(parents=True,exist_ok=True)
 hidden=[]
 for o in bpy.context.scene.objects:
  if o.name.startswith("V243_BOOT_"):o.hide_render=True;o.hide_viewport=True;hidden.append(o.name)
 coll=bpy.data.collections.get("V268_CHELSEA_BOOTS") or bpy.data.collections.new("V268_CHELSEA_BOOTS")
 if coll.name not in bpy.context.scene.collection.children:bpy.context.scene.collection.children.link(coll)
 leather=material("MAT_V268_BURNISHED_BROWN_LEATHER",(.115,.031,.012,1),.38);sole=material("MAT_V268_DARK_RUBBER_SOLE",(.012,.008,.006,1),.64);gore=material("MAT_V268_ELASTIC_GORE",(.012,.011,.011,1),.88);pieces=[]
 for side,x in (("L",-.165),("R",.165)):
  foot=loft_foot(f"V268_BOOT_FOOT_{side}",x,coll,leather);shaft=loft_shaft(f"V268_BOOT_SHAFT_{side}",x,coll,leather);base=rounded(f"V268_BOOT_SOLE_{side}",(x,-.045,.021),(.178,.318,.030),coll,sole,.010);heel=rounded(f"V268_BOOT_HEEL_{side}",(x,.078,.045),(.145,.080,.050),coll,sole,.009);sign=-1 if side=="L" else 1
  outer=rounded(f"V268_BOOT_GORE_OUTER_{side}",(x+sign*.074,.020,.220),(.006,.090,.090),coll,gore,.003);inner=rounded(f"V268_BOOT_GORE_INNER_{side}",(x-sign*.074,.020,.220),(.006,.090,.090),coll,gore,.003);tab=rounded(f"V268_BOOT_PULL_TAB_{side}",(x,.086,.322),(.024,.012,.058),coll,leather,.004)
  for o in (foot,shaft,base,heel,outer,inner,tab):parent(o,f"foot_fk.{side}");pieces.append(o)
 scene=bpy.context.scene;scene.render.engine="BLENDER_EEVEE";scene.render.image_settings.file_format="PNG";scene.view_settings.look="AgX - Medium High Contrast";cam=bpy.data.objects["CAM_V211_FRONT"]
 rig=bpy.data.objects[RIG];hr=bpy.data.objects["V250_FRETTING_HAND_RIG"];om=rig.data.pose_position;oh=hr.data.pose_position;guitar=[o for o in scene.objects if o.name.startswith("V206_")];hs={o.name:(o.hide_render,o.hide_viewport) for o in guitar};rig.data.pose_position="REST";hr.data.pose_position="REST"
 for o in guitar:o.hide_render=True;o.hide_viewport=True
 bpy.context.view_layer.update();views={"boots_front":(Vector((0,-1.55,.27)),Vector((0,-.02,.17)),82,(1100,800)),"boots_three_quarter":(Vector((-.72,-1.28,.34)),Vector((0,-.02,.17)),84,(1100,800)),"boots_profile":(Vector((-1.30,-.02,.30)),Vector((0,-.03,.17)),84,(1100,800)),"full_front":(Vector((0,-3.5,1)),Vector((0,0,1)),70,(900,1000))};renders={}
 for label,(loc,target,lens,res) in views.items():cam.location=loc;cam.data.lens=lens;point_at(cam,target);scene.camera=cam;scene.render.resolution_x,scene.render.resolution_y=res;scene.render.resolution_percentage=100;p=RENDERS/f"v268_{label}.png";scene.render.filepath=str(p);bpy.ops.render.render(write_still=True);renders[label]={"path":str(p.relative_to(ROOT)),"sha256":sha(p)}
 rig.data.pose_position=om;hr.data.pose_position=oh
 for o in guitar:o.hide_render,o.hide_viewport=hs[o.name]
 bpy.context.view_layer.update();rec={"schema":"v268-lofted-chelsea-boots-v1","status":"BUILT_VISUAL_REVIEW_REQUIRED","source":{"path":str(SOURCE.relative_to(ROOT)),"sha256":sha(SOURCE)},"hidden_old_boots":hidden,"pieces":[o.name for o in pieces],"renders":renders,"output":{"path":str(OUTPUT.relative_to(ROOT))}}
 scene["V268_STATUS"]="LOFTED_CHELSEA_BOOTS_VISUAL_REVIEW_REQUIRED";bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT),check_existing=False);rec["output"]["sha256"]=sha(OUTPUT);(AUDIT/"v268_lofted_chelsea_boots.json").write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n");print("V268_LOFTED_CHELSEA_BOOTS_OK="+json.dumps(rec,sort_keys=True))
if __name__=="__main__":main()
