"""Open free fingers and roll wrist about index tip; preserve contact pivot."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
root=Path(__file__).resolve().parents[1];out=root/'production_v452_picking_pivot';out.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
assert 'v449' in bpy.data.filepath
r=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];c=r.pose.bones['IK-Hand.R'];original=c.matrix.copy()
changes=json.loads((root/'production_v451_picking_silhouette/changes.json').read_text())
for x in changes:r.pose.bones[x['bone']].rotation_euler=x['after']
r.update_tag();bpy.context.view_layer.update()
b=r.pose.bones['DEF-Finger_Index3.R'];pivot=r.matrix_world@b.tail
axis=Vector((.5,0,-.866)).normalized()
segments=[]
for i in range(1,9):
 o=bpy.data.objects[f'V206_STRING_S{i}'];rad=o.data.bevel_depth*max(o.matrix_world.to_scale())
 for sp in o.data.splines:
  pts=[o.matrix_world@p.co.xyz for p in sp.points]
  segments.extend((i,a,z,rad) for a,z in zip(pts,pts[1:]))
trials=[];chosen=None
try:
 for mm in (12,):
  angle=-10
  transform=Matrix.Translation(pivot)@Matrix.Rotation(math.radians(angle),4,axis)@Matrix.Translation(-pivot)
  c.matrix=r.matrix_world.inverted()@Matrix.Translation(Vector((0,-mm/1000,0)))@transform@r.matrix_world@original
  r.update_tag();bpy.context.view_layer.update()
  e=bpy.data.objects['V357_ANATOMICAL_HAND.R'].evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh()
  try:tree=BVHTree.FromPolygons([e.matrix_world@v.co for v in m.vertices],[list(p.vertices) for p in m.polygons])
  finally:e.to_mesh_clear()
  hits=[];margin=1e9
  for i,a,z,rad in segments:
   d=z-a
   if d.length>1e-8 and tree.ray_cast(a,d.normalized(),d.length)[0] is not None:hits.append(i)
   n=max(1,math.ceil(d.length/.0005))
   for k in range(n+1):margin=min(margin,tree.find_nearest(a.lerp(z,k/n))[3]-.00025-rad)
  drift=((r.matrix_world@b.tail)-pivot).length
  trials.append({'outward_mm':mm,'angle':angle,'crossings':sorted(set(hits)),'clearance_m':margin,'index_pivot_drift_m':drift})
  if not hits and margin>.0003 and drift<.013:chosen={"angle":angle,"outward_mm":mm};break
finally:
 if chosen is None:
  c.matrix=original
  for x in changes:r.pose.bones[x['bone']].rotation_euler=x['before']
  r.update_tag();bpy.context.view_layer.update()
assert len(r.animation_data.drivers)==1957
(out/'report.json').write_text(json.dumps({'chosen':chosen,'trials':trials},indent=2))
print(json.dumps({'chosen':chosen,'trials':trials}))
