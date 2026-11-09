"""Remove high frequency cut-boundary noise from both sides of the seam."""
import bpy,math,json
from pathlib import Path
from mathutils import Vector,kdtree
R=Path(__file__).resolve().parents[1];O=R/'production_v420_boundary_flow';O.mkdir(exist_ok=True)
s=bpy.context.scene;o=bpy.data.objects['V416_SHARED_BOUNDARY_CUFF.R'];body=bpy.data.objects['V416_BODY_CLEAN_JOIN'];r=bpy.data.objects['V357_CLOUDRIG_CONTROLS']
assert not bpy.app.is_job_running('RENDER');assert len(r.animation_data.drivers)==1957
M=328;points=[v.co.copy() for v in list(o.data.vertices)[:M]];lens=[(points[(i+1)%M]-points[i]).length for i in range(M)];total=sum(lens);arc=[0.]
for d in lens:arc.append(arc[-1]+d)
def weights(ob,i):return {ob.vertex_groups[g.group].name:g.weight for g in ob.data.vertices[i].groups}
def setweights(ob,i,w):
 for g in list(ob.data.vertices[i].groups):ob.vertex_groups[g.group].remove([i])
 for name,value in w.items():
  if value>1e-8:ob.vertex_groups[name].add([i],value,'REPLACE')
ws=[weights(o,i) for i in range(M)];new=[];nws=[]
for i in range(M):
 coeff=[]
 for j in range(M):
  d=abs(arc[i]-arc[j]);d=min(d,total-d)
  coeff.append(math.exp(-.5*(d/.004)**2)*(lens[j-1]+lens[j])*.5 if d<.012 else 0.)
 z=sum(coeff);coeff=[x/z for x in coeff]
 new.append(sum((points[j]*a for j,a in enumerate(coeff)),Vector()))
 nws.append({n:sum(a*ws[j].get(n,0) for j,a in enumerate(coeff)) for n in set().union(*ws)})
kd=kdtree.KDTree(M)
for i,p in enumerate(points):kd.insert(p,i)
kd.balance();count=0
for v in body.data.vertices:
 if v.co.x<-.225 and .94999<=v.co.z<.97:
  _,i,d=kd.find(v.co);t=max(0.,1-(v.co.z-.95)/.02);t=t*t*(3-2*t)
  v.co+=(new[i]-points[i])*t
  if abs(v.co.z-.95)<1e-5:setweights(body,v.index,nws[i])
  count+=1
for i in range(M):o.data.vertices[i].co=new[i];setweights(o,i,nws[i])
base=984
for ring,t in ((1,.3),(2,.65)):
 for i in range(M):
  u=arc[i]/total*96;j=int(u)%96;f=u-int(u)
  target=o.data.vertices[base+j].co.lerp(o.data.vertices[base+(j+1)%96].co,f)
  a=weights(o,base+j);b=weights(o,base+(j+1)%96);lo={n:(1-f)*a.get(n,0)+f*b.get(n,0) for n in a.keys()|b.keys()}
  w={n:(1-t)*nws[i].get(n,0)+t*lo.get(n,0) for n in nws[i].keys()|lo.keys()}
  o.data.vertices[ring*M+i].co=new[i].lerp(target,t);setweights(o,ring*M+i,w)
body.data.update();o.data.update();bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(O/'Character_An_boundary_flow_v420.blend'),compress=True)
old=s.render.engine,s.render.filepath,s.camera.data.ortho_scale
try:
 s.render.engine='BLENDER_WORKBENCH';s.camera.data.ortho_scale=.35;s.render.filepath=str(O/'v420_join_diagnostic.png');bpy.ops.render.render(write_still=True)
finally:s.render.engine,s.render.filepath,s.camera.data.ortho_scale=old
(O/'report.json').write_text(json.dumps({'drivers':len(r.animation_data.drivers),'body_vertices_adjusted':count,'max_boundary_displacement_mm':max((a-b).length for a,b in zip(points,new))*1000,'status':'visual_review_pending'},indent=2))
print('V420 saved')
