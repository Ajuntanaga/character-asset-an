import bpy,json,math
from pathlib import Path
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[1];O=R/'production_v407_middle_clearance';O.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
r=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];hand=bpy.data.objects['V357_ANATOMICAL_HAND.R'];s=bpy.context.scene
b=r.pose.bones['FK-Finger_Middle1.R'];original=b.rotation_euler.x;pip=r.pose.bones['FK-Finger_Middle2.R'];oldpip=pip.rotation_euler.x;results=[];chosen=None
segments=[]
for i in range(1,9):
 o=bpy.data.objects[f'V206_STRING_S{i}']
 for sp in o.data.splines:
  assert sp.type=='POLY'
  pts=[o.matrix_world@p.co.xyz for p in sp.points]
  segments.extend((i,a,z) for a,z in zip(pts,pts[1:]))
for degrees,pipdeg in ((45,75),(55,85),(65,95),(35,100),(20,100),(0,90),(-20,90)):
 pip.rotation_euler.x=math.radians(pipdeg)
 b.rotation_euler.x=math.radians(degrees);r.update_tag();hand.update_tag();bpy.context.view_layer.update()
 e=hand.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh()
 try:tree=BVHTree.FromPolygons([e.matrix_world@v.co for v in m.vertices],[list(p.vertices) for p in m.polygons])
 finally:e.to_mesh_clear()
 hits=[]
 for i,a,z in segments:
  d=z-a
  if d.length<1e-8:continue
  if tree.ray_cast(a,d.normalized(),d.length)[0] is not None:hits.append(i)
 results.append({'middle_mcp_degrees':degrees,'middle_pip_degrees':pipdeg,'crossing_strings':sorted(set(hits))})
 if not hits:chosen=degrees;break
if chosen is None:pip.rotation_euler.x=oldpip;b.rotation_euler.x=original;r.update_tag();hand.update_tag();bpy.context.view_layer.update()
(O/'report.json').write_text(json.dumps({'before_radians':original,'chosen_degrees':chosen,'trials':results,'drivers':len(r.animation_data.drivers)},indent=2))
assert chosen is not None,'No clear candidate; pose restored'
bpy.ops.wm.save_as_mainfile(filepath=str(O/'Character_An_middle_clearance_v407.blend'),compress=True)
old=(s.render.engine,s.render.filepath)
try:s.render.engine='BLENDER_WORKBENCH';s.render.filepath=str(O/'v407_pick_diagnostic.png');bpy.ops.render.render(write_still=True)
finally:s.render.engine,s.render.filepath=old
print(json.dumps(results))
