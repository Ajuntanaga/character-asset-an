"""Fit the actual pick surface between thumb and index; preserve hand pose."""
import bpy,json,math,numpy as np
from pathlib import Path
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
root=Path('/home/ajuntanaga/Projects/Blender/Character Asset_An');out=root/'production_v504_distal_pad';data=json.loads((out/'frame.json').read_text())
assert not bpy.app.is_job_running('RENDER') and bpy.data.filepath==data['file']
r=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];p=bpy.data.objects['V361_NYLON_PICK'];g=bpy.data.objects['V206_GUITAR_ROOT'];gi=g.matrix_world.inverted()
assert len(r.animation_data.drivers)==1957
coords=[Vector(v) for v in data['hand_vertices']];groups=data['hand_groups'];faces=data['hand_faces']
whole=BVHTree.FromPolygons(coords,faces)
others=BVHTree.FromPolygons(coords,[f for f in faces if all('Finger_Thumb' not in groups[i] and 'Finger_Index' not in groups[i] for i in f)])
thumb=BVHTree.FromPolygons(coords,[f for f in faces if all('Finger_Thumb' in groups[i] for i in f)])
index=BVHTree.FromPolygons(coords,[f for f in faces if all('Finger_Index' in groups[i] for i in f)])
verts=[Vector(v) for v in data['pick_vertices']];center=sum(verts,Vector())/len(verts)
normal=(verts[48]-verts[0]).normalized();tip=(verts[0]+verts[48])*.5;direction=(tip-center).normalized();pair=data['pairs'][0];anchor=(Vector(pair['thumb'])+Vector(pair['index']))*.5;n=(Vector(pair['thumb'])-Vector(pair['index'])).normalized()
if normal.dot(n)<0:normal=-normal
align=normal.rotation_difference(n).to_matrix().to_4x4()
# Include interior points on both broad faces; boundary-only checks miss embedding.
samples=verts.copy()
for base in (0,48):
 c=sum(verts[base:base+48],Vector())/48
 for v in verts[base:base+48]:
  for t in (.25,.5,.75):samples.append(c.lerp(v,t))
def signed(tree,q):
 pos,no,idx,d=tree.find_nearest(q)
 return d*(1 if (q-pos).dot(no)>=0 else -1)
def xf_for(angle,offset,slide):
 rot=Matrix.Rotation(math.radians(angle),4,n)@align
 return Matrix.Translation(anchor+n*slide)@rot@Matrix.Translation(-center-direction*offset)
rows=[]
for angle in range(-90,91,10):
 for offset in (0,.004,.008,.012):
  for slide in (-.0005,0,.0005):
   xf=xf_for(angle,offset,slide);vv=[xf@v for v in samples];minimum=min(signed(whole,v) for v in vv);other=min(signed(others,v) for v in vv)
   th=min(abs(signed(thumb,v)) for v in vv);ind=min(abs(signed(index,v)) for v in vv);tipclear=min(signed(whole,xf@verts[i]) for i in (0,1,47,48,49,95))
   rows.append({'angle':angle,'offset':offset,'slide':slide,'minimum':minimum,'others':other,'thumb_distance':th,'index_distance':ind,'tip_clearance':tipclear})
valid=[v for v in rows if v['minimum']>-.0001 and v['others']>.0005 and v['tip_clearance']>.002]
best=min(valid,key=lambda v:(v['thumb_distance']+v['index_distance'])*1000+abs(v['angle'])*.005+abs(v['offset']-.008)*100) if valid else None
if best:
 xf=xf_for(best['angle'],best['offset'],best['slide']);p.matrix_world=g.matrix_world@xf@gi@Matrix(data['pick_world']);bpy.context.view_layer.update()
report={'selected':best,'passing':len(valid),'cases':rows};(out/'seating.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='cases'}))
