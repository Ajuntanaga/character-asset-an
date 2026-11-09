import bpy,bmesh,json,math
from pathlib import Path
from mathutils import Vector,kdtree
R=Path(__file__).resolve().parents[1];O=R/'production_v416_shared_join';O.mkdir(exist_ok=True)
s=bpy.context.scene;r=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];body=bpy.data.objects['V357_TRIPO_CHARACTER_BODY_BOUND'];cuff=bpy.data.objects['V411_FITTED_CUFF.R']
assert not bpy.app.is_job_running('RENDER');assert len(r.animation_data.drivers)==1957
assert 'V416_BODY_CLEAN_JOIN' not in bpy.data.objects
bm=bmesh.new();bm.from_mesh(body.data)
faces=[f for f in bm.faces if all(v.co.x<-.225 for v in f.verts) and any(.90<v.co.z<1.01 for v in f.verts)]
edges={e for f in faces for e in f.edges};verts={v for f in faces for v in f.verts}
bmesh.ops.bisect_plane(bm,geom=list(verts)+list(edges)+faces,plane_co=(0,0,.950),plane_no=(0,0,1),clear_inner=True,dist=1e-7)
cutverts=[v for v in bm.verts if abs(v.co.z-.950)<1e-5 and v.co.x<-.225]
bmesh.ops.remove_doubles(bm,verts=cutverts,dist=.000001)
bound=[e for e in bm.edges if e.is_boundary and all(abs(v.co.z-.950)<1e-5 and v.co.x<-.225 for v in e.verts)]
adj={}
for e in bound:
 a,b=e.verts;adj.setdefault(a,[]).append(b);adj.setdefault(b,[]).append(a)
assert all(len(ns)==2 for ns in adj.values())
start=min(adj,key=lambda v:math.atan2(v.co.y-.026,v.co.x+.294)%math.tau);loop=[start];prev=None;curr=start
while True:
 nxt=next(x for x in adj[curr] if x!=prev)
 if nxt==start:break
 loop.append(nxt);prev,curr=curr,nxt
assert len(loop)==len(adj)
# Orient around the positive local Z axis.
area=sum(a.co.x*b.co.y-b.co.x*a.co.y for a,b in zip(loop,loop[1:]+loop[:1]))
if area<0:loop=[loop[0]]+list(reversed(loop[1:]))
deflayer=bm.verts.layers.deform.active
points=[v.co.copy() for v in loop];topweights=[{body.vertex_groups[k].name:w for k,w in v[deflayer].items()} for v in loop]
newbody=body.copy();newbody.data=body.data.copy();newbody.name='V416_BODY_CLEAN_JOIN';body.users_collection[0].objects.link(newbody);bm.to_mesh(newbody.data);bm.free()
# Use exact boundary coordinates/weights at the upper ring; blend toward the existing wristband.
kd=kdtree.KDTree(len(cuff.data.vertices))
for v in cuff.data.vertices:kd.insert(v.co,v.index)
kd.balance()
def weights(idx):return {cuff.vertex_groups[g.group].name:g.weight for g in cuff.data.vertices[idx].groups}
M=len(points);vs=[];ws=[];fs=[]
for t in (0,.3,.65):
 for p,tw in zip(points,topweights):
  a=math.atan2(p.y-.026,p.x+.294);target=Vector((-.297+.028*math.cos(a),.016+.036*math.sin(a),.913))
  co=p.lerp(target,t);vs.append(co);_,idx,_=kd.find(target);lw=weights(idx);ws.append({n:(1-t)*tw.get(n,0)+t*lw.get(n,0) for n in tw.keys()|lw.keys()})
for j in range(2):
 for i in range(M):fs.append((j*M+i,(j+1)*M+i,(j+1)*M+(i+1)%M,j*M+(i+1)%M))
base=len(vs)
for v in list(cuff.data.vertices)[288:]:vs.append(v.co.copy());ws.append(weights(v.index))
# Stitch the unequal upper and lower loops in angular order.
angles=[math.atan2(p.y-.026,p.x+.294)%math.tau for p in points]
# Mesh may have shallow concave wrinkles: use monotonic cumulative arc length for safe zipper progression.
lens=[(points[(i+1)%M]-points[i]).length for i in range(M)];total=sum(lens);params=[0]
for d in lens:params.append(params[-1]+d/total)
i=j=0
while i<M or j<96:
 a=2*M+i%M;b=base+j%96
 if j==96 or (i<M and params[i+1]<(j+1)/96):fs.append((a,2*M+(i+1)%M,b));i+=1
 else:fs.append((a,base+(j+1)%96,b));j+=1
for j in range(7):
 for i in range(96):fs.append((base+j*96+i,base+(j+1)*96+i,base+(j+1)*96+(i+1)%96,base+j*96+(i+1)%96))
mesh=bpy.data.meshes.new('V416_Continuous_Sleeve_Cuff');mesh.from_pydata(vs,[],fs);mesh.update();ob=bpy.data.objects.new('V416_SHARED_BOUNDARY_CUFF.R',mesh);cuff.users_collection[0].objects.link(ob)
for mat in cuff.data.materials:mesh.materials.append(mat)
for name in {name for w in ws for name in w}:ob.vertex_groups.new(name=name)
for idx,w in enumerate(ws):
 for name,value in w.items():ob.vertex_groups[name].add([idx],value,'REPLACE')
for p in mesh.polygons:p.use_smooth=True
arm=ob.modifiers.new('Existing CloudRig deformation','ARMATURE');arm.object=r;arm.use_deform_preserve_volume=True
body.hide_render=True;body.hide_set(True);cuff.hide_render=True;cuff.hide_set(True)
bpy.context.view_layer.update()
(O/'report.json').write_text(json.dumps({'shared_boundary_vertices':M,'drivers':len(r.animation_data.drivers),'original_body_preserved':body.name,'status':'visual_review_pending'},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(O/'Character_An_shared_join_v416.blend'),compress=True)
engine,path,scale=s.render.engine,s.render.filepath,s.camera.data.ortho_scale
try:
 s.render.engine='BLENDER_WORKBENCH';s.camera.data.ortho_scale=.35;s.render.filepath=str(O/'v416_join_diagnostic.png');bpy.ops.render.render(write_still=True)
finally:s.render.engine=engine;s.render.filepath=path;s.camera.data.ortho_scale=scale
print('V416 saved; shared vertices',M)
