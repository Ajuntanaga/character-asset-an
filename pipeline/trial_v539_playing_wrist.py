"""Fit the whole picking grip to a string with a bounded rigid wrist search."""
import bpy,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
from mathutils.bvhtree import BVHTree
root=Path(__file__).resolve().parents[1];out=root/'production_v539_playing_wrist';out.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(root/'production_v538_pick_tip/Character_An_pick_tip_TRIAL_v538.blend'))
s=bpy.context.scene;main=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];hand=bpy.data.objects['V528_NATIVE_HAND.R'];rig=bpy.data.objects['V528_NATIVE_RIG.R'];pick=bpy.data.objects['V361_NYLON_PICK'];control=main.pose.bones['IK-Hand.R']
assert len(main.animation_data.drivers)==1957
original=control.matrix.copy();pb=pick.matrix_world.copy();wrist=rig.matrix_world@rig.pose.bones['DEF-Hand.R'].head
cam=s.camera;cb=cam.matrix_world.copy();cs=cam.data.ortho_scale
segments=[];allpoints=[]
for j in range(1,9):
 o=bpy.data.objects[f'V206_STRING_S{j}']
 for sp in o.data.splines:
  pp=[o.matrix_world@p.co.xyz for p in sp.points];allpoints.extend(pp)
  segments.extend((j,a,b,o.data.bevel_depth*max(o.matrix_world.to_scale())) for a,b in zip(pp,pp[1:]))
a=np.array(allpoints);origin=a.mean(axis=0);_,_,vt=np.linalg.svd(a-origin,full_matrices=False);normal=Vector(vt[-1]);normal=normal if normal.y<0 else -normal
along=(segments[0][2]-segments[0][1]).normalized();across=normal.cross(along).normalized()
tip=pb@((pick.data.vertices[0].co+pick.data.vertices[48].co)/2)
def closest(p,a,b):
 d=b-a;return a+d*max(0,min(1,(p-a).dot(d)/d.length_squared))
j,a,b,r=min(segments,key=lambda v:(closest(tip,v[1],v[2])-tip).length)
target=closest(tip,a,b)+normal*(r+.0005)
def mesh():
 e=hand.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh()
 try:return [e.matrix_world@v.co for v in m.vertices],[list(p.vertices) for p in m.polygons]
 finally:e.to_mesh_clear()
verts,faces=mesh();relative=np.array(verts)-np.array(tip);best=None
for u in range(-60,61,10):
 for v in range(-60,61,10):
  q=Quaternion(along,math.radians(u))@Quaternion(across,math.radians(v))
  if q.angle>math.radians(70):continue
  rotated=relative@np.array(q.to_matrix()).T+np.array(target)
  clearance=float(np.min((rotated-origin)@np.array(normal)))
  score=clearance-.001*q.angle
  if best is None or score>best[0]:best=(score,u,v,q,clearance)
_,u,v,q,predicted=best;delta=Matrix.Translation(target)@q.to_matrix().to_4x4()@Matrix.Translation(-tip)
try:
 desired=delta@wrist
 world=delta@main.matrix_world@original;world.translation=desired
 control.matrix=main.matrix_world.inverted()@world;bpy.context.view_layer.update()
 actual=rig.matrix_world@rig.pose.bones['DEF-Hand.R'].head
 # Match the actual evaluated donor wrist, including arm reach constraints.
 correction=actual-desired;pick.matrix_world=Matrix.Translation(correction)@delta@pb;bpy.context.view_layer.update()
 tipnow=pick.matrix_world@((pick.data.vertices[0].co+pick.data.vertices[48].co)/2)
 verts,faces=mesh();tree=BVHTree.FromPolygons(verts,faces);hits=[];margin=1e9
 for j,a,b,r in segments:
  d=b-a
  if tree.ray_cast(a,d.normalized(),d.length)[0] is not None:hits.append(j)
  n=max(1,math.ceil(d.length/.001))
  for k in range(n+1):margin=min(margin,tree.find_nearest(a.lerp(b,k/n))[3]-r)
 report={'angles_degrees':[u,v],'predicted_plane_clearance_m':predicted,'actual_min_plane_clearance_m':float(np.min((np.array(verts)-origin)@np.array(normal))),'wrist_target_error_m':correction.length,'tip_to_string_m':min((tipnow-closest(tipnow,a,b)).length-r for _,a,b,r in segments),'crossed_strings':sorted(set(hits)),'sampled_clearance_m':margin,'drivers':len(main.animation_data.drivers),'status':'WHOLE_GRIP_POSITION_TRIAL'}
 s.render.engine='BLENDER_WORKBENCH';s.render.resolution_x=900;s.render.resolution_y=900;s.render.resolution_percentage=100
 center=tipnow
 for label,pos,tar,scale in [('pinch',tuple(center+Vector((.13,-.2,.04))),tuple(center),.19),('instrument',(-.00624775,-.645,.74370837),(-.10234958,-.27,1.0414399),.42)]:
  cam.location=pos;cam.rotation_euler=(Vector(tar)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;s.render.filepath=str(out/(label+'.png'));bpy.ops.render.render(write_still=True)
 (out/'check.json').write_text(json.dumps(report,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(out/'Character_An_playing_wrist_TRIAL_v539.blend'),copy=True)
finally:
 control.matrix=original;bpy.context.view_layer.update();pick.matrix_world=pb;cam.matrix_world=cb;cam.data.ortho_scale=cs;bpy.context.view_layer.update()
print(json.dumps(report));print('V538 restored')
