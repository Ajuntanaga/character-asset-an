"""Restore iris coverage toward the facial reference without enlarging globes."""
from pathlib import Path
import bpy,json,math
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'production_v392_iris_proportions';OUT.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
rig=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];assert len(rig.animation_data.drivers)==1957
backup={}
for side in ('L','R'):
 eye=bpy.data.objects['V374_EYE.'+side];assert not eye.get('V392_applied')
 keys=eye.data.shape_keys.key_blocks
 backup[side]={'keys':{k.name:[list(v.co) for v in k.data] for k in keys}}
 basis=[v.co.copy() for v in keys[0].data]
 for i,p in enumerate(basis):
  if p.z<.005: continue
  t=max(0.,min(1.,(math.hypot(p.x,p.y)-.0035)/.0055));t=t*t*(3-2*t)
  factor=1.+.18*(1.-t)
  for k in keys:
   k.data[i].co.x*=factor;k.data[i].co.y*=factor
 cornea=bpy.data.objects['V374_CORNEA.'+side]
 backup[side]['cornea']=[list(v.co) for v in cornea.data.vertices]
 for v in cornea.data.vertices: v.co.x*=1.18;v.co.y*=1.18
 keys['Dilation'].value=.90
 eye.data.update();cornea.data.update();eye['V392_applied']=True
(OUT/'before.json').write_text(json.dumps(backup))
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Character_An_iris_proportions_v392.blend'),compress=True)
print(json.dumps({'iris_inner_scale':1.18,'drivers':len(rig.animation_data.drivers)}))
