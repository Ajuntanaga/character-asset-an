"""Bound corrective smoothing on finger weights; preserve source mesh and rig."""
import bpy,json
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'production_v463_knuckle_deformation';out.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
r=bpy.data.objects['V357_CLOUDRIG_CONTROLS']
assert r.data.pose_position=='POSE'
report={}
try:
 r.data.pose_position='REST';bpy.context.view_layer.update()
 for side in ('L','R'):
  o=bpy.data.objects['V357_ANATOMICAL_HAND.'+side]
  assert not o.modifiers.get('V463 Finger joint correction')
  group=o.vertex_groups.new(name='V463 Finger correction mask')
  indices={v.index for v in o.vertex_groups if v.name.startswith('DEF-Finger_') and not 'Thumb' in v.name}
  count=0
  for v in o.data.vertices:
   w=min(1.,sum(g.weight for g in v.groups if g.group in indices))
   if w>0:group.add([v.index],w,'REPLACE');count+=1
  mod=o.modifiers.new('V463 Finger joint correction','CORRECTIVE_SMOOTH')
  mod.factor=.5;mod.iterations=6;mod.smooth_type='LENGTH_WEIGHTED';mod.vertex_group=group.name;mod.rest_source='BIND'
  bpy.context.view_layer.objects.active=o
  with bpy.context.temp_override(object=o,active_object=o):bpy.ops.object.correctivesmooth_bind(modifier=mod.name)
  bpy.context.view_layer.update()
  report[side]={'weighted_base_vertices':count,'bound':mod.is_bind,'factor':mod.factor,'iterations':mod.iterations}
  assert mod.is_bind
finally:
 r.data.pose_position='POSE';r.update_tag();bpy.context.view_layer.update()
assert len(r.animation_data.drivers)==1957
(out/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
