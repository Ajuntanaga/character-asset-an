"""Pose-dependent dorsal MCP compression trial; neutral geometry unchanged."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1];out=root/'production_v474_joint_study'
assert not bpy.app.is_job_running('RENDER')
assert 'v473' in bpy.data.filepath
r=bpy.data.objects['V357_CLOUDRIG_CONTROLS']
source=json.loads((root/'production_v359_hand_weights/rest_hand_data.json').read_text())['bones']
report={}
for side in ('R','L'):
 o=bpy.data.objects['V357_ANATOMICAL_HAND.'+side]
 assert o.data.shape_keys is None
 o.shape_key_add(name='Basis')
 report[side]={}
 for digit in ('Middle','Ring','Pinky'):
  key=o.shape_key_add(name='V474_'+digit+'_MCP_flex')
  center=Vector(source[f'DEF-Finger_{digit}1.L']['head'])
  changed=0;maximum=0
  for v in o.data.vertices:
   if v.normal.y>-.25:continue
   weights={o.vertex_groups[w.group].name:w.weight for w in v.groups}
   if any(w>.001 and ('Thumb' in n or 'Index' in n) for n,w in weights.items()):continue
   x,y,z=v.co
   dorsal=min(1.,max(0.,(-v.normal.y-.25)/.55))
   d=.003*math.exp(-.5*(((x-center.x)/.007)**2+((z-(center.z-.006))/.011)**2))*dorsal
   if d<.00002:continue
   key.data[v.index].co.y+=d;changed+=1;maximum=max(maximum,d)
  fc=key.driver_add('value');driver=fc.driver;driver.type='SCRIPTED'
  variable=driver.variables.new();variable.name='flex';variable.type='SINGLE_PROP'
  variable.targets[0].id=r
  variable.targets[0].data_path=f'pose.bones["FK-Finger_{digit}1.{side}"].rotation_euler[0]'
  driver.expression='min(1,max(0,(flex-0.35)/0.61))'
  report[side][digit]={'vertices':changed,'max_m':maximum}
 o.data.update();o.update_tag()
assert len(r.animation_data.drivers)==1957
(out/'trial.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
p=root/'pipeline/check_v472_hand_deformation.py'
s=p.read_text().replace("production_v472_hand_deformation","production_v474_joint_study")
(out/'mode.txt').write_text('curl')
exec(compile(s,str(p),'exec'),dict(globals(),__file__=str(p)))
