"""Replace crude V242 tubes with restrained reference-matched tailoring details."""

from pathlib import Path
import hashlib, json
import bpy
from mathutils import Vector

ROOT=Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE=ROOT/"production_v262_long_sleeve_jacket"/"Character_An_long_sleeve_jacket_v262.blend"
STAGE=ROOT/"production_v263_tailoring_details"; OUTPUT=STAGE/"Character_An_tailoring_details_v263.blend"; RENDERS=STAGE/"renders"; AUDIT=STAGE/"audit"
RIG="V239_CLEAN_CHARACTER_RIG"

def sha(p):
    h=hashlib.sha256();
    with Path(p).open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""): h.update(b)
    return h.hexdigest()

def point_at(obj,target): obj.rotation_euler=(target-obj.location).to_track_quat("-Z","Y").to_euler()

def mat(name,color,rough=.68):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name); m.use_nodes=True; bs=m.node_tree.nodes.get("Principled BSDF"); bs.inputs["Base Color"].default_value=color; bs.inputs["Roughness"].default_value=rough
    if "Specular IOR Level" in bs.inputs: bs.inputs["Specular IOR Level"].default_value=.22
    return m

def parent_chest(obj):
    world=obj.matrix_world.copy(); obj.parent=bpy.data.objects[RIG]; obj.parent_type="BONE"; obj.parent_bone="chest"; obj.matrix_world=world

def mesh_obj(name,verts,faces,coll,material,thickness=.003):
    me=bpy.data.meshes.new(name+"_MESH"); me.from_pydata(verts,[],faces); me.update(); obj=bpy.data.objects.new(name,me); coll.objects.link(obj); me.materials.append(material)
    for p in me.polygons: p.use_smooth=True
    if thickness:
        sol=obj.modifiers.new(name+"_THICKNESS","SOLIDIFY"); sol.thickness=thickness; sol.offset=0
    bev=obj.modifiers.new(name+"_SOFT_EDGE","BEVEL"); bev.width=.0025; bev.segments=3
    parent_chest(obj); return obj

def lapel(name,sign,coll,material):
    inner=[(.065*sign,-.153,1.447),(.086*sign,-.184,1.365),(.108*sign,-.207,1.270),(.125*sign,-.205,1.165),(.135*sign,-.187,1.055),(.142*sign,-.165,.945)]
    outer=[(.132*sign,-.144,1.438),(.174*sign,-.166,1.355),(.190*sign,-.186,1.265),(.185*sign,-.185,1.165),(.176*sign,-.171,1.055),(.172*sign,-.153,.945)]
    verts=[co for pair in zip(inner,outer) for co in pair]; faces=[(i*2,i*2+1,i*2+3,i*2+2) for i in range(5)]
    return mesh_obj(name,verts,faces,coll,material,.004)

def main():
    if Path(bpy.data.filepath).resolve()!=SOURCE.resolve(): raise RuntimeError(f"Open V262 first: {SOURCE}")
    STAGE.mkdir(parents=True,exist_ok=True); RENDERS.mkdir(parents=True,exist_ok=True); AUDIT.mkdir(parents=True,exist_ok=True)
    hidden=[]
    for obj in bpy.context.scene.objects:
        if obj.name.startswith("V242_"):
            obj.hide_viewport=True; obj.hide_render=True; hidden.append(obj.name)
    coll=bpy.data.collections.get("V263_TAILORING_DETAILS") or bpy.data.collections.new("V263_TAILORING_DETAILS")
    if coll.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(coll)
    jacket=mat("MAT_V263_LAPEL_CHARCOAL",(.010,.011,.014,1),.74); shirt=bpy.data.materials.get("MAT_V241_FLORAL_SHIRT") or mat("MAT_V263_SHIRT",(.075,.038,.022,1),.58); trim=mat("MAT_V263_THREAD",(.035,.032,.030,1),.72); metal=mat("MAT_V263_BUTTON",(.09,.065,.035,1),.38)
    details=[lapel("V263_LAPEL_L",-1,coll,jacket),lapel("V263_LAPEL_R",1,coll,jacket)]
    # Folded shirt collar wings and narrow center placket.
    details.append(mesh_obj("V263_COLLAR_WING_L",[(-.012,-.142,1.452),(-.132,-.135,1.440),(-.102,-.183,1.365),(-.018,-.174,1.402)],[(0,1,2,3)],coll,shirt,.003))
    details.append(mesh_obj("V263_COLLAR_WING_R",[(.012,-.142,1.452),(.132,-.135,1.440),(.102,-.183,1.365),(.018,-.174,1.402)],[(0,1,2,3)],coll,shirt,.003))
    details.append(mesh_obj("V263_SHIRT_PLACKET",[(-.014,-.218,.925),(.014,-.218,.925),(.014,-.218,1.405),(-.014,-.218,1.405)],[(0,1,2,3)],coll,shirt,.002))
    # Breast pocket bodies and flaps.
    for sign,label in ((-1,"L"),(1,"R")):
        x0=.185*sign; x1=.285*sign
        details.append(mesh_obj(f"V263_BREAST_POCKET_{label}",[(x0,-.190,1.175),(x1,-.172,1.175),(x1,-.166,1.300),(x0,-.183,1.300)],[(0,1,2,3)],coll,jacket,.0035))
        details.append(mesh_obj(f"V263_POCKET_FLAP_{label}",[(x0-.006*sign,-.198,1.300),(x1+.006*sign,-.179,1.300),(x1,-.176,1.275),(x0,-.193,1.275)],[(0,1,2,3)],coll,jacket,.004))
    # Jacket and shirt button stacks.
    for x,y,z,r in [(-.162,-.202,1.238,.011),(-.157,-.192,1.115,.011),(-.151,-.176,.995,.011),(0,-.224,1.335,.0065),(0,-.224,1.255,.0065),(0,-.224,1.175,.0065),(0,-.224,1.095,.0065)]:
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,radius=r,location=(x,y,z)); obj=bpy.context.object; obj.name=f"V263_BUTTON_{len(details):02d}"; obj.scale=(1,.35,1); obj.data.materials.append(metal); parent_chest(obj); details.append(obj)
    # Narrow hem edge, replacing the oversized V242 tube.
    curve=bpy.data.curves.new("V263_HEM_STITCH_CURVE","CURVE"); curve.dimensions="3D"; curve.bevel_depth=.0012; curve.bevel_resolution=2; sp=curve.splines.new("BEZIER"); pts=[(-.205,-.150,.905),(-.10,-.166,.892),(0,-.171,.888),(.10,-.166,.892),(.205,-.150,.905)]; sp.bezier_points.add(len(pts)-1)
    for bp,co in zip(sp.bezier_points,pts): bp.co=co; bp.handle_left_type="AUTO"; bp.handle_right_type="AUTO"
    hem=bpy.data.objects.new("V263_HEM_STITCH",curve); coll.objects.link(hem); curve.materials.append(trim); parent_chest(hem); details.append(hem)
    scene=bpy.context.scene; scene.render.engine="BLENDER_EEVEE"; scene.render.image_settings.file_format="PNG"; scene.view_settings.look="AgX - Medium High Contrast"; cam=bpy.data.objects["CAM_V211_FRONT"]
    views={"full_front":(Vector((0,-3.75,1)),Vector((0,0,1)),66,(900,1000)),"upper_front":(Vector((0,-2.05,1.28)),Vector((0,0,1.25)),76,(1000,1000)),"upper_three_quarter":(Vector((-1.65,-1.85,1.32)),Vector((0,0,1.22)),82,(1000,1000))}; renders={}
    for label,(loc,target,lens,res) in views.items():
        cam.location=loc; cam.data.lens=lens; point_at(cam,target); scene.camera=cam; scene.render.resolution_x,scene.render.resolution_y=res; scene.render.resolution_percentage=100; p=RENDERS/f"v263_{label}.png"; scene.render.filepath=str(p); bpy.ops.render.render(write_still=True); renders[label]={"path":str(p.relative_to(ROOT)),"sha256":sha(p)}
    rec={"schema":"v263-tailoring-details-v1","status":"BUILT_VISUAL_REVIEW_REQUIRED","source":{"path":str(SOURCE.relative_to(ROOT)),"sha256":sha(SOURCE)},"hidden_v242":hidden,"details":[o.name for o in details],"renders":renders,"output":{"path":str(OUTPUT.relative_to(ROOT))}}
    scene["V263_STATUS"]="REFERENCE_TAILORING_DETAILS_VISUAL_REVIEW_REQUIRED"; bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT),check_existing=False); rec["output"]["sha256"]=sha(OUTPUT); (AUDIT/"v263_tailoring_details.json").write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n"); print("V263_TAILORING_DETAILS_OK="+json.dumps(rec,sort_keys=True))

if __name__=="__main__": main()
