"""Remove the last generic-body chin fragment beneath the complete FaceBuilder head."""
from pathlib import Path
import hashlib, json
import bpy
from mathutils import Vector

ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SOURCE = ROOT / "production_v331_uncut_facebuilder_head" / "Character_An_uncut_facebuilder_head_v331.blend"
STAGE = ROOT / "production_v332_remove_duplicate_chin"
OUTPUT = STAGE / "Character_An_remove_duplicate_chin_v332.blend"
RENDERS = STAGE / "renders"
AUDIT = STAGE / "audit" / "v332_remove_duplicate_chin.json"

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''): h.update(b)
    return h.hexdigest()
def aim(o,t): o.rotation_euler=(t-o.location).to_track_quat('-Z','Y').to_euler()
def render(scene,camera,path,loc,target,lens):
    camera.location=loc; camera.data.lens=lens; aim(camera,target); scene.camera=camera
    scene.render.resolution_x=scene.render.resolution_y=900; scene.render.resolution_percentage=100
    scene.render.filepath=str(path); bpy.ops.render.render(write_still=True)
    return {'path':str(path.relative_to(ROOT)),'sha256':sha(path)}
def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    for p in (STAGE,RENDERS,AUDIT.parent): p.mkdir(parents=True,exist_ok=True)
    body=bpy.data.objects['V322_MB_MALE_BODY']
    for m in list(body.modifiers):
        if m.type=='MASK' and ('BODY' in m.name or 'KEEP' in m.name): body.modifiers.remove(m)
    group=body.vertex_groups.new(name='V332_BODY_ABOVE_COLLAR')
    indices=[v.index for v in body.data.vertices if (body.matrix_world@v.co).z>1.555]
    group.add(indices,1.0,'REPLACE')
    mod=body.modifiers.new('V332_KEEP_BODY_BELOW_COLLAR','MASK'); mod.vertex_group=group.name; mod.invert_vertex_group=True
    body.modifiers.move(body.modifiers.find(mod.name),0)
    scene=bpy.context.scene; scene['V332_STATUS']='DUPLICATE_CHIN_REMOVED_VISUAL_REVIEW_REQUIRED'
    camera=bpy.data.objects['V323_CAMERA']; target=Vector((0.0,-0.065,1.665))
    renders={
      'portrait_front':render(scene,camera,RENDERS/'v332_portrait_front.png',Vector((0,-1.28,1.67)),target,104),
      'portrait_three_quarter':render(scene,camera,RENDERS/'v332_portrait_three_quarter.png',Vector((0.58,-1.16,1.70)),target,100),
    }
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT),check_existing=False)
    record={'schema':'v332-remove-duplicate-chin-v1','status':'BUILT_VISUAL_REVIEW_REQUIRED','source':{'path':str(SOURCE.relative_to(ROOT)),'sha256':sha(SOURCE)},'masked_vertices':len(indices),'renders':renders,'output':{'path':str(OUTPUT.relative_to(ROOT)),'sha256':sha(OUTPUT)}}
    AUDIT.write_text(json.dumps(record,indent=2,sort_keys=True)+'\n')
    print('V332_DUPLICATE_CHIN_OK='+json.dumps(record['output'],sort_keys=True))
if __name__=='__main__': main()
