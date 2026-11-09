import bpy,json,math
from pathlib import Path
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[1];O=R/'production_v408_clearance_margin';O.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
r=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];h=bpy.data.objects['V357_ANATOMICAL_HAND.R'];s=bpy.context.scene
bones=[r.pose.bones[f'FK-Finger_{f}{j}.R'] for f in ('Middle','Ring','Pinky') for j in (1,2,3)]
original=[list(b.rotation_euler) for b in bones]
(O/'pose_before.json').write_text(json.dumps(original))
segments=[]
for i in range(1,9):
 o=bpy.data.objects[f'V206_STRING_S{i}']
 for sp in o.data.splines:
  pts=[o.matrix_world@p.co.xyz for p in sp.points];segments.extend((i,a,z) for a,z in zip(pts,pts[1:]))
trials=[];chosen=None
try:
 for mcp,pip,dip in ((48,78,37),(51,81,39),(55,85,40)):
  for fi in range(3):
   for j,angle in enumerate((mcp+fi*3,pip+fi*3,dip+fi*2)):bones[fi*3+j].rotation_euler.x=math.radians(angle)
  r.update_tag();h.update_tag();bpy.context.view_layer.update()
  e=h.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=e.to_mesh()
  try:tree=BVHTree.FromPolygons([e.matrix_world@v.co for v in mesh.vertices],[list(p.vertices) for p in mesh.polygons])
  finally:e.to_mesh_clear()
  hits=[]
  for i,a,z in segments:
   d=z-a
   if d.length>1e-8 and tree.ray_cast(a,d.normalized(),d.length)[0] is not None:hits.append(i)
  margin=1e9
  for i,a,z in segments:
   n=max(1,math.ceil((z-a).length/.0005));o=bpy.data.objects[f'V206_STRING_S{i}'];radius=o.data.bevel_depth*max(o.matrix_world.to_scale())
   for k in range(n+1):margin=min(margin,tree.find_nearest(a.lerp(z,k/n))[3]-.00025-radius)
  trials.append({'base_angles':[mcp,pip,dip],'crossing_strings':sorted(set(hits)),'minimum_surface_margin_m':margin})
  if not hits and margin>=.001:chosen=[mcp,pip,dip];break
finally:
 if chosen is None:
  for b,rot in zip(bones,original):b.rotation_euler=rot
  r.update_tag();bpy.context.view_layer.update()
 (O/'report.json').write_text(json.dumps({'chosen':chosen,'trials':trials,'drivers':len(r.animation_data.drivers)},indent=2))
assert chosen is not None,'No clear pose; original restored'
assert len(r.animation_data.drivers)==1957
bpy.ops.wm.save_as_mainfile(filepath=str(O/'Character_An_clearance_margin_v408.blend'),compress=True)
old=(s.render.engine,s.render.filepath)
try:
 s.render.engine='BLENDER_WORKBENCH';s.render.filepath=str(O/'v408_pick_diagnostic.png');bpy.ops.render.render(write_still=True)
finally:s.render.engine,s.render.filepath=old
print(json.dumps(trials))
