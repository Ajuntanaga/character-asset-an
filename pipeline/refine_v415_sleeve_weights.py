import bpy,json
from pathlib import Path
from mathutils import Vector,kdtree
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[1];O=R/'production_v415_sleeve_weights';O.mkdir(exist_ok=True)
o=bpy.data.objects['V411_FITTED_CUFF.R'];old=bpy.data.objects['V357_CUFF_PATCH.R'];body=bpy.data.objects['V357_CUFF_PATCH.R'];r=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];s=bpy.context.scene
assert not bpy.app.is_job_running('RENDER');assert len(r.animation_data.drivers)==1957
before=json.loads((R/'production_v414_sleeve_join/before.json').read_text())
for v,co in zip(o.data.vertices,before):v.co=co
(O/'before.json').write_text(json.dumps([list(v.co) for v in o.data.vertices]))
tree=BVHTree.FromPolygons([v.co for v in old.data.vertices],[list(p.vertices) for p in old.data.polygons]);kd=kdtree.KDTree(len(body.data.vertices))
for v in body.data.vertices:kd.insert(v.co,v.index)
kd.balance();changed=0
for v in o.data.vertices:
 if v.co.z<.925:continue
 pos,n,_,_=tree.find_nearest(v.co);strength=min(1,(v.co.z-.925)/.012)
 # Upper overlap sits just inside the retained original jacket.
 radial=Vector((pos.x+.294,pos.y-.026,0)).normalized();v.co=v.co.lerp(pos-radial*.0007,strength);changed+=1
 if strength>.95:
  _,idx,_=kd.find(v.co)
  for g in list(v.groups):o.vertex_groups[g.group].remove([v.index])
  for g in body.data.vertices[idx].groups:
   name=body.vertex_groups[g.group].name;group=o.vertex_groups.get(name)
   if group is None:group=o.vertex_groups.new(name=name)
   group.add([v.index],g.weight,'REPLACE')
o.data.update();bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(O/'Character_An_sleeve_weights_v415.blend'),compress=True)
(O/'report.json').write_text(json.dumps({'changed_upper_vertices':changed,'drivers':len(r.animation_data.drivers),'status':'visual_review_pending'},indent=2))
engine,path,scale=s.render.engine,s.render.filepath,s.camera.data.ortho_scale
try:
 s.render.engine='BLENDER_WORKBENCH';s.camera.data.ortho_scale=.35;s.render.filepath=str(O/'v415_join_diagnostic.png');bpy.ops.render.render(write_still=True)
finally:s.render.engine=engine;s.render.filepath=path;s.camera.data.ortho_scale=scale
print('Saved V414',changed)
