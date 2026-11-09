from pathlib import Path
import bpy,json
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'production_v398_lip_join';OUT.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
rig=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];assert len(rig.animation_data.drivers)==1957
lips=bpy.data.objects['V363_LIPS'];body=bpy.data.objects['V357_TRIPO_CHARACTER_BODY_BOUND']
assert not lips.get('V398_applied')
lkeys=lips.data.shape_keys.key_blocks;bkeys=body.data.shape_keys.key_blocks
backup={k.name:[list(v.co) for v in k.data] for k in lkeys}
(OUT/'before_lip_join.json').write_text(json.dumps(backup))
body.data.calc_loop_triangles()
triangles=[list(t.vertices) for t in body.data.loop_triangles if all(1.49<bkeys['Basis'].data[i].co.z<1.62 and bkeys['Basis'].data[i].co.y<-.02 for i in t.vertices)]
report={}
inverse=lips.matrix_world.inverted()
for key in lkeys:
 source=bkeys.get(key.name) or bkeys['Basis']
 coords=[body.matrix_world@v.co for v in source.data]
 bvh=BVHTree.FromPolygons(coords,triangles,all_triangles=True)
 matched=0;peak=0.
 for j,weight in ((8,.3),(9,1.)):
  for i in range(96):
   index=j*96+i;p=lips.matrix_world@key.data[index].co
   hit,normal,face,distance=bvh.ray_cast(Vector((p.x,-.5,p.z)),Vector((0,1,0)))
   if hit is None:continue
   delta=(hit.y+.00012-p.y)*weight
   assert abs(delta)<.008, (key.name,index,delta)
   p.y+=delta;key.data[index].co=inverse@p
   if j==9:matched+=1
   peak=max(peak,abs(delta))
 assert matched==96,(key.name,matched)
 report[key.name]={'outer_hits':matched,'max_shift_mm':peak*1000}
lips.data.update();lips['V398_applied']=True
(OUT/'report.json').write_text(json.dumps(report,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Character_An_lip_join_v398.blend'),compress=True)
print(json.dumps(report))
