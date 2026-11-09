from pathlib import Path
import bpy, math, json
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'production_v397_lip_proportions'
OUT.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
rig=bpy.data.objects['V357_CLOUDRIG_CONTROLS']
assert len(rig.animation_data.drivers)==1957
lips=bpy.data.objects['V363_LIPS']
assert not lips.get('V397_applied')
keys=lips.data.shape_keys.key_blocks
backup={k.name:[list(v.co) for v in k.data] for k in keys}
(OUT/'before_lips.json').write_text(json.dumps(backup))
peak=0
for j in range(1,9):
 t=j/9
 profile=math.sin(math.pi*t)**2
 for i in range(96):
  theta=i*math.tau/96
  side=math.sin(theta)
  # Broaden vermilion without moving the mouth opening or patch join.
  # Paired upper peaks retain a shallow central Cupid bow.
  cupid=.72+.28*math.exp(-((abs(math.cos(theta))-.32)/.23)**2)
  dz=(.0021*cupid if side>=0 else -.00135)*profile*abs(side)**.65
  for key in keys: key.data[j*96+i].co.z+=dz
  peak=max(peak,abs(dz))
lips.data.update()
lips['V397_applied']=True
report={'max_vertical_change_mm':peak*1000,'rig_drivers':len(rig.animation_data.drivers)}
for label,indices in [('aperture',range(96)),('outer_join',range(864,960))]:
 error=max(abs(keys[k].data[i].co[a]-backup[k][i][a]) for k in backup for i in indices for a in range(3))
 assert error==0
 report[label+'_all_keys_error']=error
for key in keys:
 if key.name=='Basis':continue
 error=max(abs((key.data[i].co[a]-keys['Basis'].data[i].co[a])-(backup[key.name][i][a]-backup['Basis'][i][a])) for i in range(960) for a in range(3))
 assert error<2e-7
report['expression_deltas_preserved']=True
(OUT/'report.json').write_text(json.dumps(report,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Character_An_lip_proportions_v397.blend'),compress=True)
print(json.dumps(report))
