"""Build a thin, matte, scalp-following compact curl groom on V332."""
from pathlib import Path
import hashlib, json, math, random
import bpy
from mathutils import Vector

ROOT=Path('/home/ajuntanaga/Projects/Blender/Character Asset_An')
SOURCE=ROOT/'production_v332_remove_duplicate_chin'/'Character_An_remove_duplicate_chin_v332.blend'
STAGE=ROOT/'production_v333_scalp_following_curl_groom'
OUTPUT=STAGE/'Character_An_scalp_following_curl_groom_v333.blend'
RENDERS=STAGE/'renders'; AUDIT=STAGE/'audit'/'v333_scalp_following_curl_groom.json'

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''): h.update(b)
    return h.hexdigest()
def aim(o,t): o.rotation_euler=(t-o.location).to_track_quat('-Z','Y').to_euler()
def render(scene,cam,path,loc,target,lens):
    cam.location=loc; cam.data.lens=lens; aim(cam,target); scene.camera=cam
    scene.render.resolution_x=scene.render.resolution_y=900; scene.render.resolution_percentage=100
    scene.render.filepath=str(path); bpy.ops.render.render(write_still=True)
    return {'path':str(path.relative_to(ROOT)),'sha256':sha(path)}

def make_material():
    m=bpy.data.materials.new('V333_MELANIN_BLACK_CURLS'); m.use_nodes=True
    nt=m.node_tree; nt.nodes.clear()
    out=nt.nodes.new('ShaderNodeOutputMaterial'); diffuse=nt.nodes.new('ShaderNodeBsdfDiffuse')
    diffuse.inputs['Color'].default_value=(0.0012,0.0015,0.0020,1.0)
    diffuse.inputs['Roughness'].default_value=0.78
    nt.links.new(diffuse.outputs['BSDF'],out.inputs['Surface'])
    return m

def make_groom(material,rig):
    rng=random.Random(333)
    data=bpy.data.curves.new('V333_SCALP_CURL_GUIDES','CURVE'); data.dimensions='3D'
    data.resolution_u=1; data.bevel_depth=0.00072; data.bevel_resolution=2; data.resolution_u=2
    center=Vector((0.0,-0.064,1.728)); rx,ry,rz=0.091,0.102,0.076
    count=0
    for ring in range(1,19):
        phi=0.055+ring/19.0*1.20
        around=max(18,int(28+44*math.sin(phi)))
        for i in range(around):
            theta=math.tau*(i/around+rng.uniform(-0.006,0.006))
            # A narrow low-density lane creates the locked character-left side part.
            frontness=max(0.0,-math.sin(theta))
            if frontness>0.72 and 0.022 < rx*math.sin(phi)*math.cos(theta) < 0.040 and rng.random()<0.72:
                continue
            root=center+Vector((rx*math.sin(phi)*math.cos(theta),ry*math.sin(phi)*math.sin(theta),rz*math.cos(phi)))
            normal=Vector(((root.x-center.x)/rx,(root.y-center.y)/ry,(root.z-center.z)/rz)).normalized()
            circum=Vector((-math.sin(theta),math.cos(theta),0.0)).normalized()
            meridian=normal.cross(circum).normalized()
            radius=rng.uniform(0.0018,0.0034)
            turns=rng.uniform(0.82,1.34)
            length=rng.uniform(0.004,0.010)
            spline=data.splines.new('POLY'); steps=14; spline.points.add(steps-1)
            phase=rng.random()*math.tau
            for j in range(steps):
                t=j/(steps-1); a=phase+t*math.tau*turns
                p=root + normal*(0.0015+0.0022*t) + circum*(length*(t-0.5)+radius*math.cos(a)) + meridian*(radius*math.sin(a))
                spline.points[j].co=(*p,1.0)
            count+=1
    obj=bpy.data.objects.new('V333_COMPACT_SCALP_FOLLOWING_CURL_GROOM',data)
    bpy.context.scene.collection.objects.link(obj); data.materials.append(material)
    world=obj.matrix_world.copy(); obj.parent=rig; obj.parent_type='BONE'; obj.parent_bone='head'; obj.matrix_world=world
    return obj,count

def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    for p in (STAGE,RENDERS,AUDIT.parent): p.mkdir(parents=True,exist_ok=True)
    for name in ('V217_TIGHT_CURL_GROOM','V328_DARK_SCALP_CAP','V328_COMPACT_NATURAL_CURL_GROOM'):
        o=bpy.data.objects.get(name)
        if o: bpy.data.objects.remove(o,do_unlink=True)
    material=make_material(); groom,count=make_groom(material,bpy.data.objects['V322_MB_MALE_RIG'])
    scene=bpy.context.scene; scene['V333_STATUS']='SCALP_FOLLOWING_GROOM_VISUAL_REVIEW_REQUIRED'; scene['V333_CURL_COUNT']=count
    cam=bpy.data.objects['V323_CAMERA']; target=Vector((0.0,-0.065,1.675))
    renders={
      'front':render(scene,cam,RENDERS/'v333_groom_front.png',Vector((0,-1.28,1.69)),target,104),
      'three_quarter':render(scene,cam,RENDERS/'v333_groom_three_quarter.png',Vector((0.58,-1.16,1.71)),target,100),
      'profile':render(scene,cam,RENDERS/'v333_groom_profile.png',Vector((1.22,-0.03,1.68)),target,100),
      'rear_three_quarter':render(scene,cam,RENDERS/'v333_groom_rear_three_quarter.png',Vector((0.75,0.92,1.72)),Vector((0,0,1.71)),96),
    }
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT),check_existing=False)
    rec={'schema':'v333-scalp-following-curl-groom-v1','status':'BUILT_VISUAL_REVIEW_REQUIRED','source':{'path':str(SOURCE.relative_to(ROOT)),'sha256':sha(SOURCE)},'groom':groom.name,'curl_count':count,'renders':renders,'output':{'path':str(OUTPUT.relative_to(ROOT)),'sha256':sha(OUTPUT)}}
    AUDIT.write_text(json.dumps(rec,indent=2,sort_keys=True)+'\n'); print('V333_GROOM_OK='+json.dumps(rec['output'],sort_keys=True))
if __name__=='__main__': main()
