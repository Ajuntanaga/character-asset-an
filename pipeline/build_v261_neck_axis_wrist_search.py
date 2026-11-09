"""Coarse wrist search around the actual neck axis, then collision-aware digits."""

from pathlib import Path
import hashlib, json, math
import bpy
from mathutils import Matrix, Quaternion, Vector

ROOT=Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE=ROOT/"production_v258_collision_aware_fretting"/"Character_An_collision_aware_fretting_v258.blend"
STAGE=ROOT/"production_v261_neck_axis_wrist_search"; OUTPUT=STAGE/"Character_An_neck_axis_wrist_search_v261.blend"; RENDERS=STAGE/"renders"; AUDIT=STAGE/"audit"
LIB=ROOT/"pipeline"/"build_v258_collision_aware_fretting.py"
mod={"__name__":"v258lib"}; exec(compile(LIB.read_text(),str(LIB),"exec"),mod); mod["configure"](); base=mod["ns"]

def sha(path):
    h=hashlib.sha256();
    with Path(path).open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""): h.update(b)
    return h.hexdigest()

def point_at(obj,target): obj.rotation_euler=(target-obj.location).to_track_quat("-Z","Y").to_euler()

def main():
    if Path(bpy.data.filepath).resolve()!=SOURCE.resolve(): raise RuntimeError(f"Open V258 first: {SOURCE}")
    STAGE.mkdir(parents=True,exist_ok=True); RENDERS.mkdir(parents=True,exist_ok=True); AUDIT.mkdir(parents=True,exist_ok=True)
    rig=bpy.data.objects["V239_CLEAN_CHARACTER_RIG"]; arm=bpy.data.objects["V250_FRETTING_HAND_RIG"]; hand=bpy.data.objects["V248_FRETTING_HAND_REALISTIC"]
    neck=bpy.data.objects["V206_NECK"]; inv=neck.matrix_world.inverted(); ik=rig.pose.bones["hand_ik.L"]
    bw=rig.matrix_world@ik.matrix; bloc,brot,bscale=bw.decompose(); axis=(neck.matrix_world.to_3x3()@Vector((1,0,0))).normalized(); ny=(neck.matrix_world.to_3x3()@Vector((0,1,0))).normalized(); nz=(neck.matrix_world.to_3x3()@Vector((0,0,1))).normalized()
    contacts=base["CONTACTS"]; tv,tt=base["THUMB"]
    def set_pose(angle,dy,dz):
        q=Quaternion(axis,math.radians(angle))@brot; loc=bloc+ny*dy+nz*dz
        ik.matrix=rig.matrix_world.inverted()@Matrix.LocRotScale(loc,q,bscale); bpy.context.view_layer.update()
    def score():
        cc=sum((base["surface_world"](hand,v)-t).length_squared for v,t,_s,_f in contacts.values())+(base["surface_world"](hand,tv)-tt).length_squared
        col=0.0
        for d in ("index","middle","ring","pinky","thumb"):
            for j in range(1,4):
                b=arm.pose.bones[f"{d}_{j:02d}"]; h=arm.matrix_world@b.head; t=arm.matrix_world@b.tail
                for u in (0,.25,.5,.75,1):
                    dep=mod["collision_depth"](inv@h.lerp(t,u)); col+=dep*dep
        return cc+60*col,cc,col
    rows=[]
    for angle in (-100,-75,-50,-25,0,25,50,75,100):
        for dy in (-.04,-.02,0,.02,.04):
            for dz in (-.04,-.02,0,.02,.04):
                set_pose(angle,dy,dz); total,cc,col=score(); rows.append((total,angle,dy,dz,cc,col))
    rows.sort(key=lambda r:r[0]); best=rows[0]; set_pose(best[1],best[2],best[3])
    solves={}
    for d,(v,t,s,f) in contacts.items():
        result=mod["solve_collision"](arm,hand,d,v,t); result.update({"string":s,"fret":f}); solves[d]=result
    solves["thumb"]=mod["solve_collision"](arm,hand,"thumb",tv,tt)
    ik.keyframe_insert(data_path="location",frame=1,group=ik.name)
    if ik.rotation_mode=="QUATERNION": ik.keyframe_insert(data_path="rotation_quaternion",frame=1,group=ik.name)
    else: ik.keyframe_insert(data_path="rotation_euler",frame=1,group=ik.name)
    scene=bpy.context.scene; scene.render.engine="BLENDER_EEVEE"; scene.render.image_settings.file_format="PNG"; scene.view_settings.look="AgX - Medium High Contrast"; cam=bpy.data.objects["CAM_V211_FRONT"]
    views={"front":(Vector((.72,-1.48,1.49)),Vector((.27,-.39,1.39)),105),"oblique":(Vector((.86,-1.08,1.25)),Vector((.27,-.39,1.39)),95),"player_side":(Vector((.58,.20,1.40)),Vector((.27,-.37,1.38)),90)}; renders={}
    for label,(loc,target,lens) in views.items():
        cam.location=loc; cam.data.lens=lens; point_at(cam,target); scene.camera=cam; scene.render.resolution_x=1200; scene.render.resolution_y=900; scene.render.resolution_percentage=100
        p=RENDERS/f"v261_{label}.png"; scene.render.filepath=str(p); bpy.ops.render.render(write_still=True); renders[label]={"path":str(p.relative_to(ROOT)),"sha256":sha(p)}
    record={"schema":"v261-neck-axis-wrist-search-v1","status":"BUILT_VISUAL_REVIEW_REQUIRED","source":{"path":str(SOURCE.relative_to(ROOT)),"sha256":sha(SOURCE)},"candidates":len(rows),"best":{"score":best[0],"angle_deg":best[1],"offset_neck_y_m":best[2],"offset_neck_z_m":best[3],"contact_cost":best[4],"collision":best[5]},"top_candidates":[{"score":r[0],"angle_deg":r[1],"dy":r[2],"dz":r[3]} for r in rows[:10]],"solves":solves,"renders":renders,"output":{"path":str(OUTPUT.relative_to(ROOT))}}
    scene["V261_STATUS"]="NECK_AXIS_WRIST_SEARCH_VISUAL_REVIEW_REQUIRED"; bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT),check_existing=False); record["output"]["sha256"]=sha(OUTPUT); (AUDIT/"v261_neck_axis_wrist_search.json").write_text(json.dumps(record,indent=2,sort_keys=True)+"\n"); print("V261_NECK_AXIS_SEARCH_OK="+json.dumps(record,sort_keys=True))

if __name__=="__main__": main()
