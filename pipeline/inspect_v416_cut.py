import bpy,bmesh,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'production_v416_shared_join';O.mkdir(exist_ok=True)
o=bpy.data.objects['V357_TRIPO_CHARACTER_BODY_BOUND'];bm=bmesh.new();bm.from_mesh(o.data)
faces=[f for f in bm.faces if all(v.co.x<-.225 for v in f.verts) and any(.90<v.co.z<1.01 for v in f.verts)]
edges={e for f in faces for e in f.edges};verts={v for f in faces for v in f.verts}
bmesh.ops.bisect_plane(bm,geom=list(verts)+list(edges)+faces,plane_co=(0,0,.950),plane_no=(0,0,1),clear_inner=True,dist=1e-7)
bound=[e for e in bm.edges if e.is_boundary and all(abs(v.co.z-.950)<1e-5 and v.co.x<-.225 for v in e.verts)]
adj={}
for e in bound:
 a,b=e.verts;adj.setdefault(a,[]).append(b);adj.setdefault(b,[]).append(a)
print(json.dumps({'cut_edges':len(bound),'degree_counts':{str(k):sum(len(v)==k for v in adj.values()) for k in (1,2,3,4)},'bounds':[[min(v.co[i] for v in adj),max(v.co[i] for v in adj)] for i in range(3)]}))
ends=[v for v,ns in adj.items() if len(ns)==1]
print(json.dumps([{'p':list(v.co),'nearest_end_m':min((v.co-w.co).length for w in ends if w!=v)} for v in ends]))
bm.free()
