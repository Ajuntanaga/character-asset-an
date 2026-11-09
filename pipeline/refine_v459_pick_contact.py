import bpy,json,math
from pathlib import Path
from mathutils import Vector
root=Path('/home/ajuntanaga/Projects/Blender/Character Asset_An');out=root/'production_v459_pick_contact';out.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
p=bpy.data.objects['V361_NYLON_PICK'];g=bpy.data.objects['V206_GUITAR_ROOT'];gi=g.matrix_world.inverted()
center=Vector((.6348526776,-.0210655825,.0487754401));normal=Vector((.969659388,.148511946,.194177076)).normalized()
o=bpy.data.objects['V206_STRING_S3'];points=[gi@o.matrix_world@v.co.xyz for v in o.data.splines[0].points]
# Intersect the pick plane with a line just above the actual string surface.
radius=o.data.bevel_depth*max(o.matrix_world.to_scale());offset=Vector((0,0,radius+.0002))
candidates=[]
for a,b in zip(points,points[1:]):
 direction=b-a
 if abs(direction.dot(normal))<1e-10:continue
 t=(center-a-offset).dot(normal)/direction.dot(normal)
 if 0<=t<=1:candidates.append(a+direction*t+offset)
assert candidates, "No actual string segment intersects pick plane"
target=min(candidates,key=lambda q:(q-center).length)
forward=(target-center).normalized();across=forward.cross(normal).normalized();reach=(target-center).length
segments=[((0,reach),(.002,reach-.002),(.008,.005),(.008,0)),((.008,0),(.008,-.006),(.004,-.009),(0,-.009)),((0,-.009),(-.004,-.009),(-.008,-.006),(-.008,0)),((-.008,0),(-.008,.005),(-.002,reach-.002),(0,reach))]
outline=[]
for controls in segments:
 for i in range(12):
  t=i/12;u=1-t;weights=(u**3,3*u*u*t,3*u*t*t,t**3)
  xy=[sum(v*w for v,w in zip(axis,weights)) for axis in zip(*controls)]
  outline.append(center+across*xy[0]+forward*xy[1])
local=p.matrix_world.inverted()@g.matrix_world
verts=[list(local@(q+normal*z)) for z in (-.00035,.00035) for q in outline];n=len(outline)
faces=[list(range(n-1,-1,-1)),list(range(n,2*n))]+[[i,(i+1)%n,(i+1)%n+n,i+n] for i in range(n)]
old=p.data;mesh=bpy.data.meshes.new('V459_Contact_Pick');mesh.from_pydata(verts,[],faces);mesh.update()
for mat in old.materials:mesh.materials.append(mat)
p.data=mesh;bpy.context.view_layer.update()
report={'grip_center':list(center),'tip':list(target),'reach_mm':reach*1000,'overall_length_mm':(reach+.009)*1000,'string':3,'string_radius_mm':radius*1000,'nominal_tip_gap_mm':.2}
(out/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
cam=g.matrix_world@Vector((.68,.28,.42));look=g.matrix_world@Vector((.635,-.02,.045))
(root/'pipeline/render_preview_request.json').write_text(json.dumps({'output':'production_v459_pick_contact/v459_pick.png','resolution':[720,640],'samples':24,'scale':.23,'camera':list(cam),'target':list(look)}))
f=root/'pipeline/render_preview_job.py';exec(compile(f.read_text(),str(f),'exec'),dict(globals(),__file__=str(f)))
