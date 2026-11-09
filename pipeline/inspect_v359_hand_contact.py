"""Inspect the actual weighted hand surfaces and save isolated contact views."""
import bpy,json
from collections import Counter
from pathlib import Path
from mathutils import Vector
ROOT=Path('/home/ajuntanaga/Projects/Blender/Character Asset_An');OUT=ROOT/'production_v359_hand_weights';OUT.mkdir(exist_ok=True)
s=bpy.context.scene;g=bpy.data.objects['V206_GUITAR_ROOT'];gi=g.matrix_world.inverted();cam=s.camera
report={}
for side in ('L','R'):
 o=next(o for o in s.objects if o.name.endswith('_ANATOMICAL_HAND.'+side));ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();T=gi@ev.matrix_world
 count=Counter();minima={};positions={}
 for v in mesh.vertices:
  p=T@v.co;dominant=max(v.groups,key=lambda x:x.weight) if v.groups else None;name=o.vertex_groups[dominant.group].name if dominant else 'none'
  positions.setdefault(name,[]).append(list(p))
  width=.031+max(0,min(1,p.x/.56))*.008
  if .02<p.x<.55 and abs(p.y)<width and -.026<p.z<.015:count[name]+=1
 report[side]={'neck_inside_by_group':dict(count),'evaluated_positions':positions};ev.to_mesh_clear()
(OUT/'surface_report.json').write_text(json.dumps(report))
s.render.engine='BLENDER_WORKBENCH';s.render.threads_mode='FIXED';s.render.threads=1;s.render.resolution_x=1000;s.render.resolution_y=1000;s.render.resolution_percentage=100
cam.data.type='ORTHO'
visibility=[(o,o.hide_render) for o in s.objects if o.type=='MESH' and ('TRIPO_CHARACTER_BODY_BOUND' in o.name or 'CUFF_PATCH' in o.name)]
try:
 for label,pos,target,scale,isolate in (
  ('fretting_front',(.285,.025,.6),(.285,.025,0),.29,False),
  ('fretting_side',(.285,.48,.23),(.285,.03,0),.29,False),
  ('fretting_back',(.285,.05,-.5),(.285,.03,0),.30,True),
  ('picking_front',(.68,-.06,.6),(.68,-.06,0),.34,False)):
  for o,h in visibility:o.hide_render=True if isolate else h
  cam.location=g.matrix_world@Vector(pos);q=g.matrix_world@Vector(target);cam.rotation_euler=(q-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
  s.render.filepath=str(OUT/f'v359_{label}.png');bpy.ops.render.render(write_still=True)
finally:
 for o,h in visibility:o.hide_render=h
print(json.dumps({side:d['neck_inside_by_group'] for side,d in report.items()}))
