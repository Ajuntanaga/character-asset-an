import bpy,json,math
from pathlib import Path
from mathutils.bvhtree import BVHTree
root=Path(__file__).resolve().parents[1];out=root/'production_v507_curl_clearance';out.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
h=bpy.data.objects['V357_ANATOMICAL_HAND.R'];e=h.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();world=[e.matrix_world@v.co for v in m.vertices];tree=BVHTree.FromPolygons(world,[list(p.vertices) for p in m.polygons]);rows=[]
for i in range(1,9):
 o=bpy.data.objects[f'V206_STRING_S{i}'];rad=o.data.bevel_depth*max(o.matrix_world.to_scale());best=None
 for sp in o.data.splines:
  pts=[o.matrix_world@p.co.xyz for p in sp.points]
  for a,b in zip(pts,pts[1:]):
   n=max(1,math.ceil((b-a).length/.0005))
   for k in range(n+1):
    q=a.lerp(b,k/n);hit,normal,face,dist=tree.find_nearest(q)
    if best is None or dist<best['distance']:
     vi=min(m.polygons[face].vertices,key=lambda v:(world[v]-hit).length_squared);v=m.vertices[vi]
     best={'string':i,'distance':dist,'radius':rad,'clearance_mm':1000*(dist-rad-.00025),'vertex':vi,'group':h.vertex_groups[max(v.groups,key=lambda w:w.weight).group].name,'surface':list(hit),'string_point':list(q),'away':list((hit-q).normalized())}
 rows.append(best)
e.to_mesh_clear();(out/'contacts.json').write_text(json.dumps({'file':bpy.data.filepath,'contacts':rows},indent=2));print(json.dumps(rows))
