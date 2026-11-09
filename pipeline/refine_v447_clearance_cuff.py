"""Tailor cuff only where evaluated wrist clearance permits it."""
import bpy,math,json
from pathlib import Path
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[1];O=R/'production_v447_clearance_cuff';O.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
assert bpy.data.filepath.endswith('Character_An_cuff_fabric_v445.blend')
rig=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];assert len(rig.animation_data.drivers)==1957
c=bpy.data.objects['V357_CUFF_PATCH.L'];h=bpy.data.objects['V357_ANATOMICAL_HAND.L']
c.data=c.data.copy();base=[v.co.copy() for v in c.data.vertices]
def evaluated(o):
 bpy.context.view_layer.update();e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh()
 pts=[o.matrix_world@v.co for v in m.vertices];faces=[tuple(p.vertices) for p in m.polygons];e.to_mesh_clear();return pts,faces
hp,hf=evaluated(h)
body=bpy.data.objects['V416_BODY_CLEAN_JOIN']
e=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();offset=len(hp)
hp.extend(body.matrix_world@v.co for v in m.vertices)
hf.extend(tuple(offset+i for i in p.vertices) for p in m.polygons if p.material_index in (0,1,4,5))
e.to_mesh_clear()
tree=BVHTree.FromPolygons(hp,hf,all_triangles=False)
def clearance(p):
 q,n,i,d=tree.find_nearest(p)
 return d if (p-q).dot(n)>=0 else -d
original,_=evaluated(c);limits=[min(.002,clearance(p)) for p in original]
a=rig.data.bones['DEF-Forearm_2.L'].head_local;b=rig.data.bones['DEF-Forearm_2.L'].tail_local;axis=b-a
deltas=[]
for p0 in base:
 p=c.matrix_world@p0
 w=math.sin(math.pi*(p.z-.865)/.077)**2 if .865<p.z<.942 else 0
 center=a+axis*((p-a).dot(axis)/axis.length_squared)
 deltas.append(c.matrix_world.inverted().to_3x3()@((center-p)*(.16*w)))
def smooth(t):
 t=max(0.,min(1.,t));return t*t*(3-2*t)
weights=[smooth((tree.find_nearest(p)[3]-.020)/.030) for p in original]
adj=[set() for p in base]
for e in c.data.edges:
 i,j=e.vertices;adj[i].add(j);adj[j].add(i)
def apply():
 for i,v in enumerate(c.data.vertices):v.co=base[i]+deltas[i]*weights[i]
 c.data.update();bpy.context.view_layer.update()
for iteration in range(16):
 apply();pts,_=evaluated(c)
 bad=[i for i,p in enumerate(pts) if deltas[i].length>1e-8 and clearance(p)<limits[i]-.00002]
 if not bad:break
 for i in bad:weights[i]*=.4
 # Spread protection outward while retaining a gradual transition.
 for _ in range(3):weights=[min(w,min((weights[j]+.15 for j in adj[i]),default=w)) for i,w in enumerate(weights)]
else:
 for i in bad:weights[i]=0
 apply()
pts,_=evaluated(c)
fail=[i for i,p in enumerate(pts) if clearance(p)<limits[i]-.00002]
assert not fail, f'Clearance regressions: {len(fail)}'
report={'drivers':1957,'iterations':iteration+1,'protected_vertices':sum(w<.99 for w in weights),'max_displacement_mm':max((d*w).length*1000 for d,w in zip(deltas,weights)),'clearance_regressions_gt_0_02mm':len(fail),'scope':'Current pose vertex clearance against evaluated left hand and joined body skin; not full animation collision validation'}
(O/'report.json').write_text(json.dumps(report,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(O/'Character_An_clearance_cuff_v447.blend'),compress=True)
print(json.dumps(report))
