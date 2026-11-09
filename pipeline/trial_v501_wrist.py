import bpy,json,math
from pathlib import Path
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
root=Path('/home/ajuntanaga/Projects/Blender/Character Asset_An');out=root/'production_v501_pick_refit';assert not bpy.app.is_job_running('RENDER')
r=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];h=bpy.data.objects['V357_ANATOMICAL_HAND.R'];g=bpy.data.objects['V206_GUITAR_ROOT'];p=bpy.data.objects['V361_NYLON_PICK'];b=r.pose.bones['IK-Hand.R'];gi=g.matrix_world.inverted();orig=r.matrix_world@b.matrix;pick=p.matrix_world.copy()
(out/'wrist_pick_original.json').write_text(json.dumps({'wrist_world':[list(row) for row in orig],'pick_world':[list(row) for row in pick]}))
anchor=Vector((.635,-.020,.051));strings=[]
for i in range(1,9):
 o=bpy.data.objects[f'V206_STRING_S{i}'];rad=o.data.bevel_depth*max(o.matrix_world.to_scale())+.00025
 for sp in o.data.splines:
  pts=[o.matrix_world@p.co.xyz for p in sp.points]
  strings.extend((i,a,z,rad) for a,z in zip(pts,pts[1:]))
def setpose(deg,lift):
 xf=g.matrix_world@Matrix.Translation(Vector((0,0,lift)))@Matrix.Translation(anchor)@Matrix.Rotation(math.radians(deg),4,'Y')@Matrix.Translation(-anchor)@gi
 b.matrix=r.matrix_world.inverted()@xf@orig;bpy.context.view_layer.update();p.matrix_world=xf@pick;bpy.context.view_layer.update()
def check():
 e=h.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();tree=BVHTree.FromPolygons([e.matrix_world@v.co for v in m.vertices],[list(f.vertices) for f in m.polygons]);e.to_mesh_clear();hits=[];margin=1
 for i,a,z,rad in strings:
  d=z-a
  if tree.ray_cast(a,d.normalized(),d.length)[0] is not None:hits.append(i)
  n=max(1,math.ceil(d.length/.001))
  for k in range(n+1):margin=min(margin,tree.find_nearest(a.lerp(z,k/n))[3]-rad)
 return sorted(set(hits)),margin
rows=[]
for lift in (0,.002,.004):
 for deg in (0,-5,5,-10,10,-15,15,-20,20,-25,25):
  setpose(deg,lift);hits,margin=check();rows.append({'degrees':deg,'lift_m':lift,'hits':hits,'clearance_m':margin})
valid=[v for v in rows if not v['hits'] and v['clearance_m']>.0003]
if valid:
 best=min(valid,key=lambda v:abs(v['degrees'])+v['lift_m']*5000);setpose(best['degrees'],best['lift_m'])
else:best=None;setpose(0,0)
(out/'wrist_sweep.json').write_text(json.dumps({'selected':best,'cases':rows},indent=2));print(json.dumps({'selected':best,'passing':len(valid)}))
