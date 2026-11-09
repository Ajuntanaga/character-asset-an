"""Read-only centerline crossing check; not a full surface clearance test."""
import bpy,json
from pathlib import Path
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[1]
dg=bpy.context.evaluated_depsgraph_get();hand=bpy.data.objects['V357_ANATOMICAL_HAND.R'];e=hand.evaluated_get(dg);m=e.to_mesh()
try:
 tree=BVHTree.FromPolygons([e.matrix_world@v.co for v in m.vertices],[list(p.vertices) for p in m.polygons])
 face_groups=[]
 for poly in m.polygons:
  weights={}
  for vi in poly.vertices:
   for g in m.vertices[vi].groups:
    name=hand.vertex_groups[g.group].name;weights[name]=weights.get(name,0)+g.weight/len(poly.vertices)
  face_groups.append(sorted(weights.items(),key=lambda item:-item[1])[:3])
finally:e.to_mesh_clear()
report=[]
for i in range(1,9):
 o=bpy.data.objects[f'V206_STRING_S{i}'];hits=[];types=[]
 for sp in o.data.splines:
  types.append(sp.type)
  if sp.type!='POLY':continue
  pts=[o.matrix_world@p.co.xyz for p in sp.points]
  for a,b in zip(pts,pts[1:]):
   delta=b-a;length=delta.length
   if length<1e-8:continue
   direction=delta.normalized();offset=0.0
   for crossing in range(16):
    hit,normal,face,dist=tree.ray_cast(a+direction*offset,direction,length-offset)
    if hit is None:break
    hits.append({'point':list(hit),'distance':offset+dist,'weights':face_groups[face]})
    offset+=dist+.00001
    if offset>=length:break

 report.append({'string':o.name,'spline_types':types,'centerline_crossings':hits})
(R/'production_v406_pick_relax/string_contact.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
