"""Move unequal-loop stitching to the jacket edge; use regular quads over the taper."""
import bpy,bmesh,json,bisect
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'production_v421_regular_loft';O.mkdir(exist_ok=True)
if 'V421_REGULAR_SLEEVE_CUFF.R' in bpy.data.objects:bpy.data.objects.remove(bpy.data.objects['V421_REGULAR_SLEEVE_CUFF.R'],do_unlink=True)
s=bpy.context.scene;oldob=bpy.data.objects['V416_SHARED_BOUNDARY_CUFF.R'];r=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];assert not bpy.app.is_job_running('RENDER')
M=328;points=[v.co.copy() for v in list(oldob.data.vertices)[:M]];lens=[(points[(i+1)%M]-points[i]).length for i in range(M)];total=sum(lens);arc=[0.]
for d in lens:arc.append(arc[-1]+d/total)
def w(i):return {oldob.vertex_groups[g.group].name:g.weight for g in oldob.data.vertices[i].groups}
def mix(a,b,t):return {k:(1-t)*a.get(k,0)+t*b.get(k,0) for k in a.keys()|b.keys()}
vs=points[:];ws=[w(i) for i in range(M)];fs=[]
for t in (.18,.55):
 for j in range(96):
  u=j/96;i=min(M-1,bisect.bisect_right(arc,u)-1);f=(u-arc[i])/(arc[i+1]-arc[i]);p=points[i].lerp(points[(i+1)%M],f)
  vs.append(p.lerp(oldob.data.vertices[984+j].co,t));ws.append(mix(mix(w(i),w((i+1)%M),f),w(984+j),t))
for v in list(oldob.data.vertices)[984:]:vs.append(v.co.copy());ws.append(w(v.index))
i=j=0
while i<M or j<96:
 a=i%M;b=M+j%96
 if j==96 or (i<M and arc[i+1]<(j+1)/96):fs.append((a,(i+1)%M,b));i+=1
 else:fs.append((a,M+(j+1)%96,b));j+=1
for ring in range(9):
 for j in range(96):
  a=M+ring*96+j;b=M+ring*96+(j+1)%96
  fs.append((a,a+96,b+96,b))
mesh=bpy.data.meshes.new('V421_Regular_Loft');mesh.from_pydata(vs,[],fs);mesh.update()
bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
ob=oldob.copy();ob.data=mesh;ob.name='V421_REGULAR_SLEEVE_CUFF.R';oldob.users_collection[0].objects.link(ob)
for mat in oldob.data.materials:mesh.materials.append(mat)
for name in set().union(*(x.keys() for x in ws)):
 if name not in ob.vertex_groups:ob.vertex_groups.new(name=name)
for idx,weights in enumerate(ws):
 for name,value in weights.items():ob.vertex_groups[name].add([idx],value,'REPLACE')
for p in mesh.polygons:p.use_smooth=True
oldob.hide_render=True;oldob.hide_set(True);bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(O/'Character_An_regular_loft_v421.blend'),compress=True)
old=s.render.engine,s.render.filepath,s.camera.data.ortho_scale
try:
 s.render.engine='BLENDER_WORKBENCH';s.camera.data.ortho_scale=.35;s.render.filepath=str(O/'v421_join_diagnostic.png');bpy.ops.render.render(write_still=True)
finally:s.render.engine,s.render.filepath,s.camera.data.ortho_scale=old
print('V421 saved',len(mesh.vertices),len(r.animation_data.drivers))
