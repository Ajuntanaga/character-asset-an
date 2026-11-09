"""Apply the bounded FK fit, measure evaluated skin, and render contact views."""
import bpy,json,math
from pathlib import Path
from mathutils import Matrix,Vector
ROOT=Path('/home/ajuntanaga/Projects/Blender/Character Asset_An');OUT=ROOT/'production_v358_hand_contact'
r=next(o for o in bpy.context.scene.objects if o.name.endswith('_CLOUDRIG_CONTROLS'))
g=bpy.data.objects['V206_GUITAR_ROOT'];scene=bpy.context.scene
s=json.loads((OUT/'fretting_solution.json').read_text())
r.pose.bones['IK-Hand.L'].matrix=r.matrix_world.inverted()@g.matrix_world@Matrix(s['hand_matrix_guitar'])
for d,f in s['fingers'].items():
 a=list(map(math.radians,f['angles_degrees']))
 for i in range(1,4):
  b=r.pose.bones[f'FK-Finger_{d}{i}.L'];b.rotation_mode='XYZ';b.rotation_euler=(a[0],a[4],a[3]) if i==1 else (a[i-1],0,0)
r.update_tag();bpy.context.view_layer.update()
report={'tips':{},'surface':{},'driver_count':len(r.animation_data.drivers)}
gi=g.matrix_world.inverted()
for d,f in s['fingers'].items():
 tip=gi@r.matrix_world@r.pose.bones[f'DEF-Finger_{d}3.L'].tail
 report['tips'][d]={'actual':list(tip),'prediction_error_mm':(tip-Vector(f['points'][-1])).length*1000}
for side in ('L','R'):
 o=next(o for o in scene.objects if o.name.endswith('_ANATOMICAL_HAND.'+side))
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();T=gi@ev.matrix_world
 groups={v.index:v.name for v in o.vertex_groups};stats={};penetration=[]
 for v in mesh.vertices:
  p=T@v.co
  dominant=max(v.groups,key=lambda x:x.weight) if v.groups else None
  name=groups.get(dominant.group,'none') if dominant else 'none'
  st=stats.setdefault(name,{'count':0,'min':[1e9]*3,'max':[-1e9]*3})
  st['count']+=1
  for k in range(3):st['min'][k]=min(st['min'][k],p[k]);st['max'][k]=max(st['max'][k],p[k])
  width=.031+max(0,min(1,p.x/.56))*.008
  if .02<p.x<.55 and abs(p.y)<width and -.026<p.z<.015:
   penetration.append({'vertex':v.index,'group':name,'xyz':list(p)})
 ev.to_mesh_clear();report['surface'][side]={'bounds_by_group':stats,'neck_inside_count':len(penetration),'neck_inside_sample':penetration[:40]}
(OUT/'contact_diagnostic.json').write_text(json.dumps(report,indent=2))
scene.render.engine='BLENDER_WORKBENCH';scene.render.threads_mode='FIXED';scene.render.threads=1
scene.render.resolution_x=1000;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
camera=scene.camera;camera.data.type='ORTHO'
for label,position,target,scale in (
 ('fretting_front',(.285,.025,.60),(.285,.025,0),.29),
 ('fretting_side',(.285,.48,.23),(.285,.03,0),.29),
 ('fretting_back',(.285,.05,-.5),(.285,.03,0),.30),
 ('picking_front',(.68,-.06,.6),(.68,-.06,0),.34)):
 camera.location=g.matrix_world@Vector(position);target=g.matrix_world@Vector(target)
 camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=scale
 scene.render.filepath=str(OUT/f'v358_{label}.png');bpy.ops.render.render(write_still=True)
print(json.dumps({'tips':report['tips'],'penetration_counts':{k:v['neck_inside_count'] for k,v in report['surface'].items()}}))
