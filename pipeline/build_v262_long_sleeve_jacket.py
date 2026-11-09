"""Replace the V241 short shell with a smooth wrist-length reference jacket."""

from pathlib import Path
import hashlib, json
import bmesh, bpy
from mathutils import Vector

ROOT=Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE=ROOT/"production_v250_dedicated_hand_rig"/"Character_An_dedicated_hand_rig_v250.blend"
STAGE=ROOT/"production_v262_long_sleeve_jacket"; OUTPUT=STAGE/"Character_An_long_sleeve_jacket_v262.blend"; RENDERS=STAGE/"renders"; AUDIT=STAGE/"audit"

def sha(p):
    h=hashlib.sha256();
    with Path(p).open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""): h.update(b)
    return h.hexdigest()

def point_at(obj,target): obj.rotation_euler=(target-obj.location).to_track_quat("-Z","Y").to_euler()

def jacket_material():
    m=bpy.data.materials.get("MAT_V262_WASHED_CHARCOAL_DENIM") or bpy.data.materials.new("MAT_V262_WASHED_CHARCOAL_DENIM"); m.use_nodes=True
    n=m.node_tree.nodes; l=m.node_tree.links
    for node in tuple(n):
        if node.type not in {"BSDF_PRINCIPLED","OUTPUT_MATERIAL"}: n.remove(node)
    bs=n.get("Principled BSDF"); bs.inputs["Base Color"].default_value=(.008,.009,.011,1); bs.inputs["Roughness"].default_value=.78
    if "Specular IOR Level" in bs.inputs: bs.inputs["Specular IOR Level"].default_value=.20
    tex=n.new("ShaderNodeTexCoord"); mapping=n.new("ShaderNodeMapping"); mapping.inputs["Scale"].default_value=(115,115,115)
    w1=n.new("ShaderNodeTexWave"); w1.wave_type="BANDS"; w1.bands_direction="X"; w1.inputs["Scale"].default_value=5.0; w1.inputs["Distortion"].default_value=2.0
    w2=n.new("ShaderNodeTexWave"); w2.wave_type="BANDS"; w2.bands_direction="Y"; w2.inputs["Scale"].default_value=5.0; w2.inputs["Distortion"].default_value=2.0
    mix=n.new("ShaderNodeMixRGB"); mix.blend_type="MULTIPLY"; mix.inputs[0].default_value=.5
    bump=n.new("ShaderNodeBump"); bump.inputs["Strength"].default_value=.11; bump.inputs["Distance"].default_value=.00035
    l.new(tex.outputs["Generated"],mapping.inputs["Vector"]); l.new(mapping.outputs["Vector"],w1.inputs["Vector"]); l.new(mapping.outputs["Vector"],w2.inputs["Vector"]); l.new(w1.outputs["Color"],mix.inputs[1]); l.new(w2.outputs["Color"],mix.inputs[2]); l.new(mix.outputs["Color"],bump.inputs["Height"]); l.new(bump.outputs["Normal"],bs.inputs["Normal"])
    return m

def main():
    if Path(bpy.data.filepath).resolve()!=SOURCE.resolve(): raise RuntimeError(f"Open V250 first: {SOURCE}")
    STAGE.mkdir(parents=True,exist_ok=True); RENDERS.mkdir(parents=True,exist_ok=True); AUDIT.mkdir(parents=True,exist_ok=True)
    old=bpy.data.objects.get("V241_OPEN_JACKET")
    if old: old.hide_viewport=True; old.hide_render=True
    body=bpy.data.objects["V211_BODY_NEUTRAL"]; rig=bpy.data.objects["V239_CLEAN_CHARACTER_RIG"]
    coll=bpy.data.collections.get("V262_REFERENCE_JACKET") or bpy.data.collections.new("V262_REFERENCE_JACKET")
    if coll.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(coll)
    jacket=body.copy(); jacket.data=body.data.copy(); jacket.name="V262_LONG_SLEEVE_OPEN_JACKET"; coll.objects.link(jacket)
    for mod in tuple(jacket.modifiers): jacket.modifiers.remove(mod)
    names={g.index:g.name.lower() for g in jacket.vertex_groups}; mw=jacket.matrix_world
    bm=bmesh.new(); bm.from_mesh(jacket.data); bm.verts.ensure_lookup_table(); delete=[]
    for v in bm.verts:
        p=mw@v.co; groups={names.get(g.group,""):g.weight for g in jacket.data.vertices[v.index].groups}
        arm=max((w for name,w in groups.items() if any(t in name for t in ("upper_arm","forearm","shoulder"))),default=0.0)
        hand=max((w for name,w in groups.items() if any(t in name for t in ("hand","thumb","f_index","f_middle","f_ring","f_pinky"))),default=0.0)
        torso=.875<=p.z<=1.47 and abs(p.x)<.34
        sleeve=arm>.12 and p.z>.72 and hand<.18
        keep=torso or sleeve
        opening=p.y<-.035 and abs(p.x)<(.068+max(0,p.z-.94)*.105)
        if not keep or (opening and arm<.12): delete.append(v)
    bmesh.ops.delete(bm,geom=delete,context="VERTS"); bm.to_mesh(jacket.data); bm.free(); jacket.data.update(); jacket.data.materials.clear(); jacket.data.materials.append(jacket_material())
    sub=jacket.modifiers.new("V262_GARMENT_SUBDIVISION","SUBSURF"); sub.levels=1; sub.render_levels=2
    disp=jacket.modifiers.new("V262_BODY_CLEARANCE","DISPLACE"); disp.mid_level=.5; disp.strength=.014
    solid=jacket.modifiers.new("V262_FABRIC_THICKNESS","SOLIDIFY"); solid.thickness=.0045; solid.offset=.15
    smooth=jacket.modifiers.new("V262_SURFACE_RELAX","SMOOTH"); smooth.factor=.08; smooth.iterations=2
    armature=jacket.modifiers.new("V262_RIG","ARMATURE"); armature.object=rig; armature.use_deform_preserve_volume=True
    for poly in jacket.data.polygons: poly.use_smooth=True
    jacket["v262_reference_long_sleeve"]=True
    scene=bpy.context.scene; scene.render.engine="BLENDER_EEVEE"; scene.render.image_settings.file_format="PNG"; scene.view_settings.look="AgX - Medium High Contrast"; cam=bpy.data.objects["CAM_V211_FRONT"]
    views={"full_front":(Vector((0,-3.75,1.0)),Vector((0,0,1.0)),66,(900,1000)),"upper_front":(Vector((0,-2.05,1.28)),Vector((0,0,1.25)),76,(1000,1000)),"upper_three_quarter":(Vector((-1.65,-1.85,1.32)),Vector((0,0,1.22)),82,(1000,1000))}; renders={}
    for label,(loc,target,lens,res) in views.items():
        cam.location=loc; cam.data.lens=lens; point_at(cam,target); scene.camera=cam; scene.render.resolution_x,scene.render.resolution_y=res; scene.render.resolution_percentage=100
        p=RENDERS/f"v262_{label}.png"; scene.render.filepath=str(p); bpy.ops.render.render(write_still=True); renders[label]={"path":str(p.relative_to(ROOT)),"sha256":sha(p)}
    rec={"schema":"v262-long-sleeve-jacket-v1","status":"BUILT_VISUAL_REVIEW_REQUIRED","source":{"path":str(SOURCE.relative_to(ROOT)),"sha256":sha(SOURCE)},"jacket":{"object":jacket.name,"vertices":len(jacket.data.vertices),"polygons":len(jacket.data.polygons)},"renders":renders,"output":{"path":str(OUTPUT.relative_to(ROOT))}}
    scene["V262_STATUS"]="REFERENCE_LONG_SLEEVE_JACKET_VISUAL_REVIEW_REQUIRED"; bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT),check_existing=False); rec["output"]["sha256"]=sha(OUTPUT); (AUDIT/"v262_long_sleeve_jacket.json").write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n"); print("V262_LONG_SLEEVE_JACKET_OK="+json.dumps(rec,sort_keys=True))

if __name__=="__main__": main()
