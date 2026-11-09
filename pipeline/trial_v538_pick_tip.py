"""Orient the existing plectrum tip toward strings without changing finger anatomy."""
import bpy,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
from mathutils.bvhtree import BVHTree
root=Path(__file__).resolve().parents[1];out=root/'production_v538_pick_tip';out.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(root/'production_v537_opposed_contact/Character_An_opposed_contact_TRIAL_v537.blend'))
s=bpy.context.scene;pick=bpy.data.objects['V361_NYLON_PICK'];hand=bpy.data.objects['V528_NATIVE_HAND.R'];main=bpy.data.objects['V357_CLOUDRIG_CONTROLS']
assert len(main.animation_data.drivers)==1957
pb=pick.matrix_world.copy();cam=s.camera;cb=cam.matrix_world.copy();cs=cam.data.ortho_scale
points=[pb@v.co for v in pick.data.vertices];assert len(points)==96
center=sum(points,Vector())/len(points);tip=(points[0]+points[48])/2;back=(points[24]+points[72])/2
axis=(tip-back).normalized();normal=(points[48]-points[0]).normalized()
segments=[]
for j in range(1,9):
 o=bpy.data.objects[f'V206_STRING_S{j}']
 for sp in o.data.splines:
  pp=[o.matrix_world@p.co.xyz for p in sp.points]
  segments.extend((j,a,b,o.data.bevel_depth*max(o.matrix_world.to_scale())) for a,b in zip(pp,pp[1:]))
def closest(p,a,b):
 d=b-a;return a+d*max(0,min(1,(p-a).dot(d)/d.length_squared))
target=min((closest(center,a,b) for _,a,b,_ in segments),key=lambda p:(p-center).length)
direction=target-center;direction=(direction-normal*direction.dot(normal)).normalized()
angle=math.atan2(normal.dot(axis.cross(direction)),axis.dot(direction));rot=Quaternion(normal,angle).to_matrix().to_4x4()
# Place contact 12 mm behind the point, leaving a playable exposed tip.
contact=tip-axis*.012
try:
 pick.matrix_world=Matrix.Translation(center)@rot@Matrix.Translation(-contact)@pb;bpy.context.view_layer.update()
 tip=pick.matrix_world@((pick.data.vertices[0].co+pick.data.vertices[48].co)/2)
 e=hand.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh()
 try:tree=BVHTree.FromPolygons([e.matrix_world@v.co for v in m.vertices],[list(p.vertices) for p in m.polygons])
 finally:e.to_mesh_clear()
 hits=[];margin=1e9
 for j,a,b,r in segments:
  d=b-a
  if tree.ray_cast(a,d.normalized(),d.length)[0] is not None:hits.append(j)
  for k in range(max(1,math.ceil(d.length/.001))+1):
   p=a.lerp(b,k/max(1,math.ceil(d.length/.001)));margin=min(margin,tree.find_nearest(p)[3]-r)
 report={'tip_world':list(tip),'rotation_degrees':math.degrees(angle),'tip_to_nearest_string_m':min((tip-closest(tip,a,b)).length-r for _,a,b,r in segments),'hand_crossed_strings':sorted(set(hits)),'hand_sampled_string_clearance_m':margin,'tip_nearest_skin_m':tree.find_nearest(tip)[3],'drivers':len(main.animation_data.drivers),'status':'TIP_ORIENTATION_TRIAL_REQUIRES_REVIEW'}
 s.render.engine='BLENDER_WORKBENCH';s.render.resolution_x=900;s.render.resolution_y=900;s.render.resolution_percentage=100
 for label,pos,target,scale in [('pinch',tuple(center+Vector((.13,-.2,.04))),tuple(center),.16),('instrument',(-.00624775,-.645,.74370837),(-.10234958,-.27,1.0614399),.42)]:
  cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;s.render.filepath=str(out/(label+'.png'));bpy.ops.render.render(write_still=True)
 (out/'check.json').write_text(json.dumps(report,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(out/'Character_An_pick_tip_TRIAL_v538.blend'),copy=True)
finally:
 pick.matrix_world=pb;cam.matrix_world=cb;cam.data.ortho_scale=cs;bpy.context.view_layer.update()
print(json.dumps(report));print('V537 pick restored')
