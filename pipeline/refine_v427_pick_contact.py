"""Resolve enlarged picking hand string crossing with bounded wrist adjustment."""
import bpy,json,math
from pathlib import Path
from mathutils.bvhtree import BVHTree
from mathutils import Vector
root=Path(__file__).resolve().parents[1];out=root/'production_v427_pick_contact';out.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
assert 'v426' in bpy.data.filepath
rig=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];ctrl=rig.pose.bones['IK-Hand.R'];original=ctrl.matrix.copy()
h=bpy.data.objects['V357_ANATOMICAL_HAND.R'];segments=[]
for i in range(1,9):
 o=bpy.data.objects[f'V206_STRING_S{i}'];rad=o.data.bevel_depth*max(o.matrix_world.to_scale())
 for sp in o.data.splines:
  pts=[o.matrix_world@p.co.xyz for p in sp.points]
  segments.extend((i,a,z,rad) for a,z in zip(pts,pts[1:]))
trials=[];chosen=None
try:
 for mm in (0,2,4,6,8):
  mat=original.copy();mat.translation+=rig.matrix_world.inverted().to_3x3()@Vector((0,-mm/1000,0));ctrl.matrix=mat
  rig.update_tag();bpy.context.view_layer.update()
  e=h.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=e.to_mesh()
  try:tree=BVHTree.FromPolygons([e.matrix_world@v.co for v in mesh.vertices],[list(p.vertices) for p in mesh.polygons])
  finally:e.to_mesh_clear()
  hits=[];margin=1e9
  for i,a,z,rad in segments:
   d=z-a
   if d.length>1e-8 and tree.ray_cast(a,d.normalized(),d.length)[0] is not None:hits.append(i)
   n=max(1,math.ceil(d.length/.0005))
   for k in range(n+1):margin=min(margin,tree.find_nearest(a.lerp(z,k/n))[3]-.00025-rad)
  trials.append({'outward_mm':mm,'crossing_strings':sorted(set(hits)),'margin_m':margin})
  if not hits and margin>=.001:chosen=mm;break
finally:
 if chosen is None:ctrl.matrix=original;rig.update_tag();bpy.context.view_layer.update()
assert chosen is not None,trials
assert len(rig.animation_data.drivers)==1957
(out/'report.json').write_text(json.dumps({'trials':trials,'chosen_mm':chosen,'drivers':1957,'status':'Picking string clearance checked; visual review and fretting contact remain'},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(out/'Character_An_pick_contact_v427.blend'))
print(json.dumps(trials))
