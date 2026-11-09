"""Apply the saved contact fit and inspect the evaluated skin on both hands."""
import bpy,json,math
from collections import Counter
from pathlib import Path
from mathutils import Matrix,Vector
ROOT=Path('/home/ajuntanaga/Projects/Blender/Character Asset_An');OUT=ROOT/'production_v360_hand_clearance'
s=bpy.context.scene;r=next(o for o in s.objects if o.name.endswith('_CLOUDRIG_CONTROLS'));g=bpy.data.objects['V206_GUITAR_ROOT'];gi=g.matrix_world.inverted()
report={}
for side,filename in (('L','fretting_solution.json'),('R','picking_solution.json')):
 solution=json.loads((OUT/filename).read_text())
 r.pose.bones['IK-Hand.'+side].matrix=r.matrix_world.inverted()@g.matrix_world@Matrix(solution['hand_matrix_guitar'])
 for d,f in solution['fingers'].items():
  a=list(map(math.radians,f['angles_degrees']))
  for i in range(1,4):
   b=r.pose.bones[f'FK-Finger_{d}{i}.{side}'];b.rotation_mode='XYZ';b.rotation_euler=(a[0],a[4],a[3]) if i==1 else (a[i-1],0,0)
 r.update_tag();bpy.context.view_layer.update()
 tips={d:(gi@r.matrix_world@r.pose.bones[f'DEF-Finger_{d}3.{side}'].tail-Vector(f['points'][-1])).length*1000 for d,f in solution['fingers'].items()}
 o=next(o for o in s.objects if o.name.endswith('_ANATOMICAL_HAND.'+side));ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();T=gi@ev.matrix_world
 count=Counter();positions={}
 for v in mesh.vertices:
  p=T@v.co;dom=max(v.groups,key=lambda x:x.weight) if v.groups else None;name=o.vertex_groups[dom.group].name if dom else 'none'
  positions.setdefault(name,[]).append(list(p));width=.031+max(0,min(1,p.x/.56))*.008
  if .02<p.x<.55 and abs(p.y)<width and -.026<p.z<.015:count[name]+=1
 ev.to_mesh_clear();report[side]={'prediction_error_mm':tips,'neck_inside_by_group':dict(count),'evaluated_positions':positions}
(OUT/'surface_report.json').write_text(json.dumps(report))
s.render.engine='BLENDER_WORKBENCH';s.render.threads_mode='FIXED';s.render.threads=1;s.render.resolution_x=1000;s.render.resolution_y=1000;s.render.resolution_percentage=100;cam=s.camera;cam.data.type='ORTHO'
visibility=[(o,o.hide_render) for o in s.objects if o.type=='MESH' and ('TRIPO_CHARACTER_BODY_BOUND' in o.name or 'CUFF_PATCH' in o.name)]
try:
 for label,pos,target,scale,isolate in (
  ('fretting_front',(.285,.025,.6),(.285,.025,0),.29,False),
  ('fretting_side',(.285,.48,.23),(.285,.03,0),.29,False),
  ('fretting_back',(.285,.05,-.5),(.285,.03,0),.30,True),
  ('picking_front',(.68,-.06,.6),(.68,-.06,0),.34,False),
  ('picking_side',(.68,.40,.20),(.68,-.04,.04),.30,True)):
  for o,h in visibility:o.hide_render=True if isolate else h
  cam.location=g.matrix_world@Vector(pos);q=g.matrix_world@Vector(target);cam.rotation_euler=(q-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
  s.render.filepath=str(OUT/f'v360_{label}.png');bpy.ops.render.render(write_still=True)
finally:
 for o,h in visibility:o.hide_render=h
print(json.dumps({side:{k:v for k,v in d.items() if k!='evaluated_positions'} for side,d in report.items()}))
