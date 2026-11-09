import bpy,json,math
from pathlib import Path
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
root=Path('/home/ajuntanaga/Projects/Blender/Character Asset_An');out=root/'production_v502_pick_contact';out.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER') and 'v501' in bpy.data.filepath
r=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];h=bpy.data.objects['V357_ANATOMICAL_HAND.R'];g=bpy.data.objects['V206_GUITAR_ROOT'];p=bpy.data.objects['V361_NYLON_PICK'];b=r.pose.bones['IK-Hand.R'];gi=g.matrix_world.inverted();orig=r.matrix_world@b.matrix;pick=p.matrix_world.copy()
assert len(r.animation_data.drivers)==1957
backup={'wrist_world':[list(row) for row in orig],'pick_world':[list(row) for row in pick]};
if not (out/'original_pose.json').exists(): (out/'original_pose.json').write_text(json.dumps(backup,indent=2))
tip_id=min(range(len(p.data.vertices)),key=lambda i:(gi@pick@p.data.vertices[i].co).z);tip=gi@pick@p.data.vertices[tip_id].co
strings=[]
for i in range(1,9):
 o=bpy.data.objects[f'V206_STRING_S{i}'];rad=o.data.bevel_depth*max(o.matrix_world.to_scale())
 for sp in o.data.splines:
  pts=[gi@o.matrix_world@v.co.xyz for v in sp.points]
  strings.extend((i,a,z,rad) for a,z in zip(pts,pts[1:]))
_,a,z,rad=next(s for s in strings if s[0]==4 and min(s[1].x,s[2].x)<=tip.x<=max(s[1].x,s[2].x));target=a.lerp(z,(tip.x-a.x)/(z.x-a.x));target.z+=rad+.0001
# Evaluate the rigid hand in guitar space once; wrist transformations preserve shape.
e=h.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();coords=[gi@e.matrix_world@v.co for v in m.vertices];faces=[list(f.vertices) for f in m.polygons];e.to_mesh_clear()
def xf_for(x,y):return Matrix.Translation(target)@Matrix.Rotation(math.radians(x),4,'X')@Matrix.Rotation(math.radians(y),4,'Y')@Matrix.Translation(-tip)
def check(xf):
 tree=BVHTree.FromPolygons([xf@v for v in coords],faces);hits=[];margin=1
 for i,a,z,rad in strings:
  d=z-a
  if tree.ray_cast(a,d.normalized(),d.length)[0] is not None:hits.append(i)
  n=max(1,math.ceil(d.length/.001))
  for k in range(n+1):margin=min(margin,tree.find_nearest(a.lerp(z,k/n))[3]-rad-.00025)
 return sorted(set(hits)),margin
rows=[]
for x in range(-50,51,10):
 for y in range(-50,51,10):
  hits,margin=check(xf_for(x,y));rows.append({'x_deg':x,'y_deg':y,'hits':hits,'clearance_m':margin})
valid=[v for v in rows if not v['hits'] and v['clearance_m']>.0003]
best=min(valid,key=lambda v:v['x_deg']**2+v['y_deg']**2) if valid else None
if best:
 xf=g.matrix_world@xf_for(best['x_deg'],best['y_deg'])@gi;b.matrix=r.matrix_world.inverted()@xf@orig;bpy.context.view_layer.update();p.matrix_world=xf@pick;bpy.context.view_layer.update()
report={'selected':best,'passing':len(valid),'tip_vertex':tip_id,'original_tip':list(tip),'target':list(target),'cases':rows};(out/'sweep.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='cases'}))
