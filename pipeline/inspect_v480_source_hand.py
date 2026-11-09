import bpy,json
from pathlib import Path
from mathutils import Vector
root=Path('/home/ajuntanaga/Projects/Blender/Character Asset_An')
out=root/'production_v480_hand_source_review';out.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
assert bpy.data.scenes.get('V480_SOURCE_REVIEW') is None
with bpy.data.libraries.load(str(root/'third_party/cc0_hands/innerscene/hand-posable-right.blend'),link=False) as (src,dst):
 dst.objects=src.objects
s=bpy.data.scenes.new('V480_SOURCE_REVIEW')
objects=[o for o in dst.objects if o]
for o in objects:s.collection.objects.link(o)
report=[]
for o in objects:
 report.append({'name':o.name,'type':o.type,'dimensions':list(o.dimensions),'bounds':[list(o.matrix_world@Vector(c)) for c in o.bound_box] if o.type=='MESH' else None})
(out/'inventory.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
