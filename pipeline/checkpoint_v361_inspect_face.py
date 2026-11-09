"""Save the grip/cuff checkpoint, then render the actual dense head for fitting."""
import bpy, json, math
from pathlib import Path
from mathutils import Matrix, Vector

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'production_v361_pick_cuffs'
FACE=ROOT/'production_v362_face_anatomy'; FACE.mkdir(exist_ok=True)
s=bpy.context.scene
r=next(o for o in s.objects if o.name.endswith('_CLOUDRIG_CONTROLS'))
g=bpy.data.objects['V206_GUITAR_ROOT']
toggle=bpy.data.objects['V206_CONTROL_SWITCH_TOGGLE']
toggle.parent=g; toggle.matrix_parent_inverse=Matrix.Identity(4); toggle.matrix_basis=Matrix.Identity(4)
pick=bpy.data.objects['V361_NYLON_PICK']
wrist=r.pose.bones['IK-Hand.R']
bpy.context.view_layer.update(); before=pick.matrix_world.copy(); basis=wrist.matrix_basis.copy()
wrist.matrix_basis=basis@Matrix.Rotation(math.radians(2),4,'X')
r.update_tag();bpy.context.view_layer.update(); moved=pick.matrix_world.copy()
wrist.matrix_basis=basis;r.update_tag();bpy.context.view_layer.update()
movement=(moved.translation-before.translation).length
rotation=(moved.to_quaternion().rotation_difference(before.to_quaternion())).angle
if rotation<.01:raise RuntimeError('Plectrum did not follow its hand control')
report={'pick_rotation_test_degrees':math.degrees(rotation),'pick_origin_movement_mm':movement*1000,'rig_driver_count':len(r.animation_data.drivers),'selector_parent':toggle.parent.name}
(OUT/'parenting_check.json').write_text(json.dumps(report,indent=2))
save=OUT/'Character_An_picking_grip_cuffs_v361.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(save),compress=True)

body=next(o for o in s.objects if o.name.endswith('_TRIPO_CHARACTER_BODY_BOUND'))
coords=[body.matrix_world@v.co for v in body.data.vertices]
indices=[i for i,p in enumerate(coords) if p.z>1.48]
chosen=set(indices)
faces=[list(p.vertices) for p in body.data.polygons if all(i in chosen for i in p.vertices)]
data={'object':body.name,'matrix_world':list(map(list,body.matrix_world)),
      'vertices':{str(i):list(coords[i]) for i in indices},'faces':faces,
      'face_bones':{b.name:{'head':list(b.head_local),'tail':list(b.tail_local),'parent':b.parent.name if b.parent else None,'deform':b.use_deform} for b in r.data.bones if any(k in b.name for k in ('Eye','Lid','Jaw','Mouth','Lip','Head'))},
      'materials':[m.name for m in body.data.materials],
      'images':[(im.name,list(im.size),im.filepath) for im in bpy.data.images if im.size[0]>128]}
(FACE/'head_geometry.json').write_text(json.dumps(data))
s.render.engine='BLENDER_WORKBENCH';s.render.threads_mode='FIXED';s.render.threads=1
s.render.resolution_x=1200;s.render.resolution_y=1200;s.render.resolution_percentage=100
cam=s.camera;cam.data.type='ORTHO';cam.data.ortho_scale=.40
s.display.shading.color_type='TEXTURE'
for label,pos,target in [('front',(0,-1.4,1.68),(0,0,1.68)),('three_quarter',(.8,-1.2,1.68),(0,0,1.68)),('profile',(1.4,0,1.68),(0,0,1.68))]:
    cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler()
    s.render.filepath=str(FACE/f'v362_before_{label}.png');bpy.ops.render.render(write_still=True)
print(json.dumps({'checkpoint':str(save),'head_vertices':len(indices),'head_faces':len(faces),'rig':report,'materials':data['materials'],'images':data['images']}))
