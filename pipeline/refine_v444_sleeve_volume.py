"""Tailor forearm sleeve volume coherently across the joined body and cuffs."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];O=R/'production_v444_sleeve_volume';O.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
assert bpy.data.filepath.endswith('Character_An_eye_aperture_v443.blend')
rig=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];assert len(rig.animation_data.drivers)==1957
names=['V416_BODY_CLEAN_JOIN','V357_CUFF_PATCH.L','V421_REGULAR_SLEEVE_CUFF.R','V411_Cuff_Stitches.R','V413_Brass_Cuff_Button.R']
report={}
def smooth(t):
 t=max(0,min(1,t));return t*t*(3-2*t)
for name in names:
 o=bpy.data.objects[name];o.data=o.data.copy(); changes={}
 jacket=set()
 if name=='V416_BODY_CLEAN_JOIN':
  for p in o.data.polygons:
   if p.material_index==6:jacket.update(p.vertices)
 for v in o.data.vertices:
  p=o.matrix_world@v.co
  if not .915<p.z<1.17 or abs(p.x)<.22:continue
  if name=='V416_BODY_CLEAN_JOIN' and v.index not in jacket:continue
  side='L' if p.x>0 else 'R'
  a=rig.matrix_world@rig.data.bones['DEF-Forearm_1.'+side].head_local
  b=rig.matrix_world@rig.data.bones['DEF-Forearm_2.'+side].tail_local
  axis=b-a;t=(p-a).dot(axis)/axis.length_squared;c=a+axis*t
  if (p-c).length>.115:continue
  weight=smooth((p.z-.915)/.045)*smooth((1.17-p.z)/.09)
  delta=o.matrix_world.inverted().to_3x3()@((c-p)*(.20*weight))
  changes[v.index]=delta
 if o.data.shape_keys:
  for key in o.data.shape_keys.key_blocks:
   for i,d in changes.items():key.data[i].co+=d
 else:
  for i,d in changes.items():o.data.vertices[i].co+=d
 o.data.update();report[name]={'changed':len(changes),'max_mm':max((d.length*1000 for d in changes.values()),default=0)}
bpy.context.view_layer.update()
(O/'report.json').write_text(json.dumps(report,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(O/'Character_An_sleeve_volume_v444.blend'),compress=True)
print(json.dumps(report))
