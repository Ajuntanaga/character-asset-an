import bpy,json,math
from mathutils.bvhtree import BVHTree
from pathlib import Path
root=Path('/home/ajuntanaga/Projects/Blender/Character Asset_An')
h=bpy.data.objects['V357_ANATOMICAL_HAND.R'];e=h.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh()
try:
 finite=all(math.isfinite(c) for v in m.vertices for c in v.co)
 tree=BVHTree.FromPolygons([e.matrix_world@v.co for v in m.vertices],[list(p.vertices) for p in m.polygons])
 count=len(m.vertices)
finally:e.to_mesh_clear()
hits=[];margin=1e9
for i in range(1,9):
 o=bpy.data.objects[f'V206_STRING_S{i}'];rad=o.data.bevel_depth*max(o.matrix_world.to_scale())
 for sp in o.data.splines:
  pts=[o.matrix_world@p.co.xyz for p in sp.points]
  for a,z in zip(pts,pts[1:]):
   d=z-a
   if d.length>1e-8 and tree.ray_cast(a,d.normalized(),d.length)[0] is not None:hits.append(i)
   n=max(1,math.ceil(d.length/.0005))
   for k in range(n+1):margin=min(margin,tree.find_nearest(a.lerp(z,k/n))[3]-.00025-rad)
r={'finite':finite,'vertices':count,'crossed_string_centrelines':sorted(set(hits)),'sampled_clearance_m':margin,'drivers':len(bpy.data.objects['V357_CLOUDRIG_CONTROLS'].animation_data.drivers)}
(root/'production_v458_grip_fit/check.json').write_text(json.dumps(r,indent=2));print(json.dumps(r))
