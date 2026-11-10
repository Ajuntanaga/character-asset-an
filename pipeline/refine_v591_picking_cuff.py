"""Isolated cuff fitting trial; no rig or hand edits."""
import json
from pathlib import Path
KEY='V591_CuffFit'
NAMES=('V421_REGULAR_SLEEVE_CUFF.R','V411_Cuff_Stitches.R','V413_Brass_Cuff_Button.R')
def fit_cuff(output):
 import bpy
 from mathutils import Vector
 cuff=bpy.data.objects[NAMES[0]]
 centers=[sum((cuff.data.vertices[i].co for i in range(328+r*96,328+(r+1)*96)),Vector())/96 for r in range(10)]
 # Restore a wearable circumference: current posed opening 220 mm, trial 176 mm.
 factors=[1.,.95,.88,.80,.80,.80,.80,.80,.80,.80]
 def deform(p):
  pairs=sorted(zip(centers,factors),key=lambda x:x[0].z)
  c,f=pairs[0] if p.z<=pairs[0][0].z else pairs[-1]
  for (a,fa),(b,fb) in zip(pairs,pairs[1:]):
   if a.z<=p.z<=b.z:
    t=(p.z-a.z)/(b.z-a.z);c=a.lerp(b,t);f=fa+(fb-fa)*t;break
  q=p.copy();q.x=c.x+(p.x-c.x)*f;q.y=c.y+(p.y-c.y)*f;return q
 report=[]
 for name in NAMES:
  ob=bpy.data.objects[name]
  if ob.data.shape_keys is None:ob.shape_key_add(name='Basis',from_mix=False)
  basis=ob.data.shape_keys.key_blocks['Basis'];key=ob.shape_key_add(name=KEY,from_mix=False)
  for a,b in zip(key.data,basis.data):a.co=b.co
  transform=cuff.matrix_world.inverted()@ob.matrix_world;inverse=transform.inverted()
  if ob==cuff:
   for r,(c,f) in enumerate(zip(centers,factors)):
    for i in range(328+r*96,328+(r+1)*96):
     p=basis.data[i].co;q=key.data[i].co;q.x=c.x+(p.x-c.x)*f;q.y=c.y+(p.y-c.y)*f
  elif 'Button' in name:
   c=sum((transform@p.co for p in basis.data),Vector())/len(basis.data);delta=inverse.to_3x3()@(deform(c)-c)
   for p in key.data:p.co+=delta
  else:
   for p,b in zip(key.data,basis.data):p.co=inverse@deform(transform@b.co)
  key.value=1;ob.data.update();report.append({'object':name,'peak_mm':max((ob.matrix_world.to_3x3()@(p.co-b.co)).length for p,b in zip(key.data,basis.data))*1000})
 bpy.context.view_layer.update()
 Path(output,'cuff-fit-report.json').write_text(json.dumps(report,indent=2));return report


def build(output):
 import bpy
 hand=bpy.data.objects['V528_NATIVE_HAND.R']
 donor=bpy.data.objects['V528_NATIVE_RIG.R']
 assert len(bpy.data.objects['V357_CLOUDRIG_CONTROLS'].animation_data.drivers)==1957
 assert not hand.vertex_groups.get('V591_ExposedHand')
 assert all(not bpy.data.objects[n].data.shape_keys or KEY not in bpy.data.objects[n].data.shape_keys.key_blocks for n in NAMES)
 report={'cuff':fit_cuff(output),'status':'INTERMEDIATE_REQUIRES_TEXTURED_AND_DEFORMATION_REVIEW'}
 # Mesh and donor share a coordinate system; do not apply posed coordinates.
 assert max(abs(hand.matrix_world[i][j]-donor.matrix_world[i][j]) for i in range(4) for j in range(4))<1e-6
 wrist=donor.data.bones['DEF-Hand.R'].head_local
 axis=(donor.data.bones['DEF-Finger_Middle1.R'].head_local-wrist).normalized()
 group=hand.vertex_groups.new(name='V591_ExposedHand')
 kept=[v.index for v in hand.data.vertices if (v.co-wrist).dot(axis)>=0.0]
 assert len(hand.data.vertices)-len(kept)==75
 group.add(kept,1.,'REPLACE')
 mask=hand.modifiers.new('V591_CoveredForearm','MASK')
 mask.vertex_group=group.name
 # Subdivision interpolates weights; a zero threshold leaves a thin skin flap.
 mask.threshold=.999
 mask.use_smooth=True
 report.update(masked_base_vertices=75,mask_threshold=.999,hand_pose_changed=False,main_drivers=1957)
 bpy.context.view_layer.update()
 Path(output,'picking-cuff-report.json').write_text(json.dumps(report,indent=2))
 return report
