import bpy,json,collections
from pathlib import Path
R=Path(__file__).resolve().parents[1];o=bpy.data.objects['V357_CUFF_PATCH.R'];m=o.data
edges=collections.Counter(tuple(sorted((p.vertices[i],p.vertices[(i+1)%len(p.vertices)]))) for p in m.polygons for i in range(len(p.vertices)))
adj=collections.defaultdict(set)
for (a,b),n in edges.items():
 if n==1:adj[a].add(b);adj[b].add(a)
seen=set();components=[]
for start in adj:
 if start in seen:continue
 stack=[start];comp=[]
 while stack:
  v=stack.pop()
  if v in seen:continue
  seen.add(v);comp.append(v);stack.extend(adj[v]-seen)
 components.append(comp)
report={'matrix':[list(row) for row in o.matrix_world],'boundary_components':[{'count':len(c),'bounds':[[min(m.vertices[i].co[j] for i in c),max(m.vertices[i].co[j] for i in c)] for j in range(3)],'degrees':dict(collections.Counter(len(adj[i]) for i in c))} for c in components],'groups':[g.name for g in o.vertex_groups],'materials':dict(collections.Counter(p.material_index for p in m.polygons))}
(R/'production_v408_clearance_margin/cuff_topology.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
