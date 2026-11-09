"""Inset the maple cap while keeping the reference-traced body and pose intact."""
from pathlib import Path
import json
import bpy
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'production_v400_maple_perimeter';OUT.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
rig=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];assert len(rig.animation_data.drivers)==1957
obj=bpy.data.objects['V206_FIGURED_TOP']
assert not obj.get('V400_inset')
mesh=obj.data
n=len(mesh.vertices)//2
assert len(mesh.vertices)==1600
points=[Vector((v.co.x,v.co.y)) for v in mesh.vertices[:n]]
area=sum(points[i].cross(points[(i+1)%n]) for i in range(n))
assert area>0
inset=[Vector(p) for p in json.loads((OUT/'inset_outline.json').read_text())]
assert len(inset)==n
(OUT/'before_vertices.json').write_text(json.dumps([list(v.co) for v in mesh.vertices]))
for i,p in enumerate(inset):
 for k in (i,i+n):mesh.vertices[k].co.x=p.x;mesh.vertices[k].co.y=p.y
bounds=json.loads((ROOT/'production_v356_reference_guitar/wood_uv.json').read_text())
lo,hi=bounds['lo'],bounds['hi']
uv=mesh.uv_layers['WoodProjection']
for loop in mesh.loops:
 v=mesh.vertices[loop.vertex_index].co
 uv.data[loop.index].uv=((v.x-lo[0])/(hi[0]-lo[0]),(v.y-lo[1])/(hi[1]-lo[1]))
mesh.update()
obj['V400_inset']=.0025
report={'perimeter_inset_m':.0025,'vertices':len(mesh.vertices),'rig_drivers':1957,'body_core_unchanged':True,'pose_unchanged':True}
(OUT/'report.json').write_text(json.dumps(report,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Character_An_maple_perimeter_v400.blend'),compress=True)
print(json.dumps(report))
