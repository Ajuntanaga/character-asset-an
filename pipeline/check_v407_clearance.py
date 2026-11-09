import bpy,json,math
from pathlib import Path
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[1];h=bpy.data.objects['V357_ANATOMICAL_HAND.R'];e=h.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh()
try:tree=BVHTree.FromPolygons([e.matrix_world@v.co for v in m.vertices],[list(p.vertices) for p in m.polygons])
finally:e.to_mesh_clear()
report=[];step=.00005
for i in range(1,9):
 o=bpy.data.objects[f'V206_STRING_S{i}'];best=1e9
 for sp in o.data.splines:
  pts=[o.matrix_world@p.co.xyz for p in sp.points]
  for a,b in zip(pts,pts[1:]):
   n=max(1,math.ceil((b-a).length/step))
   for j in range(n+1):best=min(best,tree.find_nearest(a.lerp(b,j/n))[3])
 radius=o.data.bevel_depth*max(o.matrix_world.to_scale())
 report.append({'string':o.name,'sampled_center_distance_m':best,'radius_m':radius,'conservative_surface_clearance_m':best-step/2-radius})
(R/'production_v407_unused_clearance/clearance.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
