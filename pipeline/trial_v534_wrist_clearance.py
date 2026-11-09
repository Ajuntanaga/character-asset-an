"""Lift picking wrist above string plane through IK, preserving seated pick."""
import bpy,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
root=Path(__file__).resolve().parents[1];out=root/'production_v534_wrist_clearance';out.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(root/'production_v533_pick_seating/Character_An_thumb_surface_TRIAL_v533.blend'))
scene=bpy.context.scene;main=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];hand=bpy.data.objects['V528_NATIVE_HAND.R'];rig=bpy.data.objects['V528_NATIVE_RIG.R'];pick=bpy.data.objects['V361_NYLON_PICK'];control=main.pose.bones['IK-Hand.R']
assert len(main.animation_data.drivers)==1957 and not bpy.app.is_job_running('RENDER')
segments=[];points=[]
for i in range(1,9):
 o=bpy.data.objects[f'V206_STRING_S{i}'];radius=o.data.bevel_depth*max(o.matrix_world.to_scale())
 for sp in o.data.splines:
  p=[o.matrix_world@x.co.xyz for x in sp.points];points.extend(p)
  segments.extend((i,a,b,radius) for a,b in zip(p,p[1:]))
a=np.array(points);center=a.mean(axis=0);_,_,vt=np.linalg.svd(a-center,full_matrices=False);normal=Vector(vt[-1])
if normal.y>0:normal=-normal
origin=Vector(center)
def meshdata():
 e=hand.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh()
 try:return [e.matrix_world@v.co for v in m.vertices],[list(p.vertices) for p in m.polygons]
 finally:e.to_mesh_clear()
def check():
 verts,faces=meshdata();tree=BVHTree.FromPolygons(verts,faces);hits=[];margin=1e9
 for i,a,b,r in segments:
  d=b-a
  if d.length<1e-8:continue
  if tree.ray_cast(a,d.normalized(),d.length)[0] is not None:hits.append(i)
  n=max(1,math.ceil(d.length/.001))
  for k in range(n+1):margin=min(margin,tree.find_nearest(a.lerp(b,k/n))[3]-r)
 return {'crossed_strings':sorted(set(hits)),'sampled_surface_clearance_m':margin,'min_plane_distance_m':min((v-origin).dot(normal) for v in verts)}
backup=control.matrix.copy();pb=pick.matrix_world.copy();wrist=rig.matrix_world@rig.pose.bones['DEF-Hand.R'].head
cam=scene.camera;cb=cam.matrix_world.copy();cs=cam.data.ortho_scale
settings=(scene.render.engine,scene.render.resolution_x,scene.render.resolution_y,scene.render.resolution_percentage,scene.render.filepath)
try:
 before=check();required=max(0,.002-before['min_plane_distance_m']);assert required<.10,required
 desired=wrist+normal*required
 for iteration in range(12):
  current=rig.matrix_world@rig.pose.bones['DEF-Hand.R'].head;delta=desired-current
  if delta.length<.0001:break
  mat=control.matrix.copy();mat.translation+=main.matrix_world.to_3x3().inverted()@delta;control.matrix=mat;bpy.context.view_layer.update()
 actual=rig.matrix_world@rig.pose.bones['DEF-Hand.R'].head-wrist
 pick.matrix_world=pb;pick.matrix_world.translation+=actual;bpy.context.view_layer.update()
 after=check();report={'before':before,'after':after,'required_lift_m':required,'actual_wrist_delta':list(actual),'normal':list(normal),'drivers':len(main.animation_data.drivers),'status':'CLEARANCE_TRIAL_NOT_FINAL_GRIP'}
 scene.render.engine='BLENDER_WORKBENCH';scene.render.resolution_x=900;scene.render.resolution_y=900;scene.render.resolution_percentage=100
 for label,pos,target,scale in [('instrument',(-.00624775,-.645,.74370837),(-.10234958,-.27,1.0314399),.42),('pinch',(.027,-.48,1.07),(-.11,-.29,1.03),.19),('character',(.35,-3.5,1.3),(0,0,.94),2.12)]:
  cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;scene.render.filepath=str(out/(label+'.png'));bpy.ops.render.render(write_still=True)
 (out/'check.json').write_text(json.dumps(report,indent=2))
 bpy.ops.wm.save_as_mainfile(filepath=str(out/'Character_An_wrist_clearance_TRIAL_v534.blend'),copy=True)
finally:
 control.matrix=backup;bpy.context.view_layer.update();pick.matrix_world=pb;cam.matrix_world=cb;cam.data.ortho_scale=cs
 scene.render.engine,scene.render.resolution_x,scene.render.resolution_y,scene.render.resolution_percentage,scene.render.filepath=settings
 bpy.context.view_layer.update()
print(json.dumps(report));print('V533 restored')
