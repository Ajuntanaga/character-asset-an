import bpy,json
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];O=R/'production_v418_sleeve_flow';O.mkdir(exist_ok=True);o=bpy.data.objects['V416_SHARED_BOUNDARY_CUFF.R'];s=bpy.context.scene
assert not bpy.app.is_job_running('RENDER')
M=328
for ring in (1,2):
 ids=list(range(ring*M,(ring+1)*M));coords=[o.data.vertices[i].co.copy() for i in ids];weights=[{g.group:g.weight for g in o.data.vertices[i].groups} for i in ids]
 for step in range(16):
  coords=[coords[i]*.5+(coords[(i-1)%M]+coords[(i+1)%M])*.25 for i in range(M)]
  weights=[{g:.5*weights[i].get(g,0)+.25*(weights[(i-1)%M].get(g,0)+weights[(i+1)%M].get(g,0)) for g in weights[i].keys()|weights[(i-1)%M].keys()|weights[(i+1)%M].keys()} for i in range(M)]
 for idx,co,w in zip(ids,coords,weights):
  v=o.data.vertices[idx];v.co=co
  for g in list(v.groups):o.vertex_groups[g.group].remove([idx])
  for g,value in w.items():o.vertex_groups[g].add([idx],value,'REPLACE')
o.data.update();bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(O/'Character_An_sleeve_flow_v418.blend'),compress=True)
engine,path,scale=s.render.engine,s.render.filepath,s.camera.data.ortho_scale
try:
 s.render.engine='BLENDER_WORKBENCH';s.camera.data.ortho_scale=.35;s.render.filepath=str(O/'v418_join_diagnostic.png');bpy.ops.render.render(write_still=True)
finally:s.render.engine=engine;s.render.filepath=path;s.camera.data.ortho_scale=scale
print('V418 saved')
