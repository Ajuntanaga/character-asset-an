"""Match loft position and skin interpolation to the existing zipper parameter."""
import bpy,json,math
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'production_v419_loft_correspondence';O.mkdir(exist_ok=True)
s=bpy.context.scene;o=bpy.data.objects['V416_SHARED_BOUNDARY_CUFF.R'];r=bpy.data.objects['V357_CLOUDRIG_CONTROLS']
assert not bpy.app.is_job_running('RENDER');assert len(r.animation_data.drivers)==1957
M=328;base=3*M
points=[o.data.vertices[i].co.copy() for i in range(M)]
lens=[(points[(i+1)%M]-points[i]).length for i in range(M)];total=sum(lens);params=[0.]
for d in lens:params.append(params[-1]+d/total)
def weights(i):return {g.group:g.weight for g in o.data.vertices[i].groups}
def blend(a,b,t):return {k:(1-t)*a.get(k,0)+t*b.get(k,0) for k in a.keys()|b.keys()}
for ring,t in ((1,.3),(2,.65)):
 for i,p in enumerate(points):
  u=params[i]*96;j=int(u)%96;f=u-int(u)
  target=o.data.vertices[base+j].co.lerp(o.data.vertices[base+(j+1)%96].co,f)
  v=o.data.vertices[ring*M+i];v.co=p.lerp(target,t)
  w=blend(weights(i),blend(weights(base+j),weights(base+(j+1)%96),f),t)
  for g in list(v.groups):o.vertex_groups[g.group].remove([v.index])
  for g,value in w.items():o.vertex_groups[g].add([v.index],value,'REPLACE')
o.data.update();bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(O/'Character_An_loft_correspondence_v419.blend'),compress=True)
old=s.render.engine,s.render.filepath,s.camera.data.ortho_scale
try:
 s.render.engine='BLENDER_WORKBENCH';s.camera.data.ortho_scale=.35;s.render.filepath=str(O/'v419_join_diagnostic.png');bpy.ops.render.render(write_still=True)
finally:s.render.engine,s.render.filepath,s.camera.data.ortho_scale=old
(O/'report.json').write_text(json.dumps({'drivers':len(r.animation_data.drivers),'shared_boundary_vertices':M,'pose_changed':False,'status':'visual_review_pending'},indent=2))
print('V419 saved')
