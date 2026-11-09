import bpy,json,math
from pathlib import Path
from mathutils import Matrix
from mathutils.bvhtree import BVHTree
root=Path('/home/ajuntanaga/Projects/Blender/Character Asset_An');out=root/'production_v502_pick_contact'
assert not bpy.app.is_job_running('RENDER') and 'v501' in bpy.data.filepath
r=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];h=bpy.data.objects['V357_ANATOMICAL_HAND.R'];p=bpy.data.objects['V361_NYLON_PICK']
assert len(r.animation_data.drivers)==1957
names=[f'FK-Finger_Middle{i}.R' for i in (1,2,3)]
f=out/'middle_original.json';assert not f.exists()
backup={n:[list(row) for row in r.pose.bones[n].matrix_basis] for n in names};f.write_text(json.dumps(backup))
points=[p.matrix_world@p.data.vertices[i].co for i in (0,1,48)]
def apply(angles):
 for n,m,a in zip(names,backup.values(),angles):
  b=r.pose.bones[n];b.matrix_basis=Matrix(m);b.rotation_euler.x=math.radians(a)
 r.update_tag();bpy.context.view_layer.update()
def check():
 e=h.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();tree=BVHTree.FromPolygons([e.matrix_world@v.co for v in m.vertices],[list(f.vertices) for f in m.polygons]);e.to_mesh_clear()
 result=[]
 for q in points:
  pos,normal,idx,d=tree.find_nearest(q);result.append(d*(1 if (q-pos).dot(normal)>=0 else -1))
 return min(result)
rows=[]
try:
 for a in (0,10,20):
  for b in (65,80,95):
   for c in (50,65,80):
    apply((a,b,c));rows.append({'angles':[a,b,c],'pick_tip_clearance_m':check()})
 valid=[v for v in rows if v['pick_tip_clearance_m']>.001]
 best=min(valid,key=lambda v:sum((a-b)**2 for a,b in zip(v['angles'],(10,65,50)))) if valid else None
 (out/'middle_sweep.json').write_text(json.dumps({'selected':best,'cases':rows},indent=2));print(json.dumps({'selected':best,'best_clearance':max(v['pick_tip_clearance_m'] for v in rows)}))
finally:
 for n,m in backup.items():r.pose.bones[n].matrix_basis=Matrix(m)
 r.update_tag();bpy.context.view_layer.update()
if best:apply(best['angles'])
