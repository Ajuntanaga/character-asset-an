"""Fit Antonia donor with joint landmarks and native skin weights; isolated trial."""
import bpy,numpy as np,json,bmesh
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1];out=root/'production_v521_donor_fit';out.mkdir(exist_ok=True)
h=bpy.data.objects['V357_ANATOMICAL_HAND.R'];rig=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];assert len(rig.animation_data.drivers)==1957
assert not bpy.app.is_job_running('RENDER')
sb=json.loads((root/'production_v520_donor_fit/source_bones.json').read_text())['metarig-antonia']
tb=json.loads((root/'production_v359_hand_weights/rest_hand_data.json').read_text())['bones']
with bpy.data.libraries.load(str(root/'production_v519_source_anatomy/Antonia_hand_donor_v519.blend'),link=False) as (src,dst):dst.objects=['V519_ANTONIA_HAND_DONOR']
o=dst.objects[0];o.name='V521_ANTONIA_HAND_TRIAL';bpy.context.scene.collection.objects.link(o);o.matrix_world=h.matrix_world
src=[];target=[]
for short,long in [('f_index','Index'),('f_middle','Middle'),('f_ring','Ring'),('f_pinky','Pinky'),('thumb','Thumb')]:
 for j in (1,2,3):
  a=sb[f'{short}.{j:02d}.L'];b=tb[f'DEF-Finger_{long}{j}.L']
  src.append(a['head']);target.append(b['head'])
  if j==3:src.append(a['tail']);target.append(b['tail'])
# Add wrist and an off-plane landmark to constrain depth and handedness.
local=h.matrix_world.inverted()@rig.matrix_world
wrist=local@rig.data.bones['DEF-Hand.R'].head_local
src.append(sb['hand.L']['head']);target.append(list(wrist))
# Derive depth from the actual palm plane, rather than a world axis.
sa=np.array(src);ta=np.array(target)
def palm_frame(points):
 along=points[4]-points[20];along/=np.linalg.norm(along)
 across=points[0]-points[12];across-=along*np.dot(across,along);across/=np.linalg.norm(across)
 normal=np.cross(across,along);normal/=np.linalg.norm(normal)
 return along,across,normal
sl,sw,sn=palm_frame(sa);tl,tw,tn=palm_frame(ta)
length_scale=np.linalg.norm(ta[4]-ta[20])/np.linalg.norm(sa[4]-sa[20])
width_scale=np.linalg.norm(ta[0]-ta[12])/np.linalg.norm(sa[0]-sa[12])
depth_scale=min(length_scale,width_scale)
for source_point,target_point in zip(sa,ta):
 for sign in (-1,1):
  src.append(list(source_point+sign*.012*sn));target.append(list(target_point+sign*.012*depth_scale*tn))
# Constrain the wrist cross section and proximal crop to the palm frame.
for proximal in (0,.025,.05):
 for lateral in (-.025,0,.025):
  for depth in (-.012,.012):
   src.append(list(sa[20]-sl*proximal+sw*lateral+sn*depth))
   target.append(list(ta[20]-tl*proximal*length_scale+tw*lateral*width_scale+tn*depth*depth_scale))
a=np.array(src);b=np.array(target);center=a.mean(axis=0);a-=center
# Polyharmonic interpolation with affine tail maps original joints exactly.
d=np.linalg.norm(a[:,None,:]-a[None,:,:],axis=2);p=np.column_stack([np.ones(len(a)),a]);system=np.block([[d+np.eye(len(a))*1e-8,p],[p.T,np.zeros((4,4))]])
coef=np.linalg.solve(system,np.vstack([b,np.zeros((4,3))]))
x=np.array([v.co[:] for v in o.data.vertices])-center
mapped=np.column_stack([np.linalg.norm(x[:,None,:]-a[None,:,:],axis=2),np.ones(len(x)),x])@coef
for v,c in zip(o.data.vertices,mapped):v.co=c
bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(o.data);bm.free()
ids=json.loads((root/'production_v519_source_anatomy/antonia_vertex_map.json').read_text())['original_vertex_ids'];lookup={v:i for i,v in enumerate(ids)}
z=np.load(root/'third_party/charmorph/v0.4.0-3/CharMorph-data/characters/antonia/weights/rigify.npz');names=bytes(z['names']).decode().split('\0');offset=0
weights=[{} for _ in ids]
for name,count in zip(names,z['cnt']):
 count=int(count);indices=z['idx'][offset:offset+count];values=z['weights'][offset:offset+count];offset+=count
 if not name.startswith('DEF-') or not name.endswith('.L'):continue
 dest='DEF-Hand.R'
 for short,long in [('f_index','Index'),('f_middle','Middle'),('f_ring','Ring'),('f_pinky','Pinky'),('thumb','Thumb')]:
  for j in (1,2,3):
   if name==f'DEF-{short}.{j:02d}.L':dest=f'DEF-Finger_{long}{j}.R'
 for index,value in zip(indices,values):
  if int(index) in lookup:
   row=weights[lookup[int(index)]];row[dest]=row.get(dest,0)+float(value)
for row in weights:
 if not row:row['DEF-Hand.R']=1
for name in sorted({n for row in weights for n in row}):
 group=o.vertex_groups.new(name=name)
 for i,row in enumerate(weights):
  if name in row:group.add([i],row[name]/sum(row.values()),'REPLACE')
arm=o.modifiers.new('CloudRig native transferred weights','ARMATURE');arm.object=rig;arm.use_deform_preserve_volume=False
bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_move_up(modifier=arm.name)
o.data.materials.clear()
for mat in h.data.materials:o.data.materials.append(mat)
for poly in o.data.polygons:poly.material_index=1 if poly.material_index in (5,6) else 0
names=[f'FK-Finger_{f}{j}.R' for f in ('Index','Middle','Ring','Pinky') for j in (1,2,3)];pose={n:rig.pose.bones[n].matrix_basis.copy() for n in names}
def render(label):
 bpy.context.view_layer.update();f=root/'pipeline/review_v492_isolated_palm.py'
 code=f.read_text().replace("bpy.data.objects['V357_ANATOMICAL_HAND.R']","bpy.data.objects['V521_ANTONIA_HAND_TRIAL']").replace('production_v492_palm_review','production_v521_donor_fit/'+label).replace('out.mkdir(exist_ok=True)','out.mkdir(parents=True,exist_ok=True)')
 exec(compile(code,str(f),'exec'),{'__file__':str(f)})
try:
 render('playing')
 for n in names:rig.pose.bones[n].rotation_euler.x=0
 render('open')
 (out/'fit.json').write_text(json.dumps({'vertices':len(mapped),'finite':bool(np.isfinite(mapped).all()),'landmarks':len(a),'weights_normalized':True,'drivers':len(rig.animation_data.drivers)},indent=2))
 # Retain fitted geometry and native weights separately, without embedding the character rig.
 o.modifiers.remove(arm);bpy.data.libraries.write(str(out/'Antonia_fitted_hand_v521.blend'),{o},fake_user=True)
finally:
 for n,m in pose.items():rig.pose.bones[n].matrix_basis=m
 data=o.data;bpy.data.objects.remove(o,do_unlink=True);bpy.data.meshes.remove(data);bpy.context.view_layer.update()
print('V521 trial rendered; original scene and pose restored')
