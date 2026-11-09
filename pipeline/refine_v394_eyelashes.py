"""Tapered lashes following the existing lid margins and their blink keys."""
from pathlib import Path
import bpy,math,random,json
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'production_v394_eyelashes';OUT.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
rig=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];assert len(rig.animation_data.drivers)==1957
from mathutils.bvhtree import BVHTree
body=bpy.data.objects['V357_TRIPO_CHARACTER_BODY_BOUND']
lidmat=list(body.data.materials).index(bpy.data.materials['V365_LID_SKIN'])
basis=body.data.shape_keys.key_blocks['Basis']
surface=BVHTree.FromPolygons([v.co for v in basis.data],[list(p.vertices) for p in body.data.polygons if any(1.625<basis.data[i].co.z<1.675 for i in p.vertices)],all_triangles=False)
rng=random.Random(394);report={}
for side in ('L','R'):
 name='V394_EYELASHES.'+side
 if name in bpy.data.objects:bpy.data.objects.remove(bpy.data.objects[name],do_unlink=True)
 margin=bpy.data.objects['V369_LID_MARGIN.'+side];keys=margin.data.shape_keys.key_blocks
 edges={key.name:[sum((key.data[i*6+k].co for k in range(6)),Vector())/6 for i in range(64)] for key in keys}
 closed=body.data.shape_keys.key_blocks['Blink.'+side]
 closed_surface=BVHTree.FromPolygons([v.co for v in closed.data],[list(p.vertices) for p in body.data.polygons if any(1.625<basis.data[i].co.z<1.675 for i in p.vertices)],all_triangles=False)
 neutral=edges['Basis'];xmin=min(p.x for p in neutral);xmax=max(p.x for p in neutral)
 states={key:[] for key in edges};faces=[];count=0
 for upper,n in ((True,54),(False,27)):
  for j in range(n):
   f=(j+.35+rng.random()*.3)/n
   pos=(1+30*f) if upper else (33+30*f)
   i=int(pos);a=pos-i
   root=neutral[i].lerp(neutral[(i+1)%64],a)
   u=(root.x-xmin)/(xmax-xmin)
   length=(.0022 if upper else .00115)*rng.uniform(.7,1.2)*(.45+.55*math.sin(math.pi*u))
   sideways=(u-.5)*.55
   direction=Vector((sideways,-.75,.75 if upper else -.65)).normalized()
   # A curved shaft projects toward the viewer before turning away from the aperture.
   base=len(states['Basis']);radius=rng.uniform(.000025,.000040)
   tangent=Vector((1,0,0));cross=direction.cross(tangent).normalized()
   for key,edge in edges.items():
    p=edge[i].lerp(edge[(i+1)%64],a)
    for step in range(6):
     t=step/5
     q=p+direction*length*t+Vector((0,-length*.35*math.sin(math.pi*t),0))
     if key in ('Basis','Blink'):
      active_surface=surface if key=='Basis' else closed_surface
      hit,_,_,_=active_surface.ray_cast(Vector((q.x,-.3,q.z)),Vector((0,1,0)),.4)
      if hit is not None:q.y=min(q.y,hit.y-.00010-.00045*t)
     rad=radius*(1-t)**.8+.000002
     for k in range(3):
      states[key].append(q+rad*(tangent*math.cos(k*math.tau/3)+cross*math.sin(k*math.tau/3)))
   for step in range(5):
    for k in range(3):
     faces.append((base+step*3+k,base+step*3+(k+1)%3,base+(step+1)*3+(k+1)%3,base+(step+1)*3+k))
   count+=1
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(states['Basis'],[],faces);mesh.update()
 obj=bpy.data.objects.new(name,mesh);bpy.context.scene.collection.objects.link(obj)
 obj.parent=margin.parent;obj.parent_type=margin.parent_type;obj.parent_bone=margin.parent_bone
 obj.matrix_parent_inverse=margin.matrix_parent_inverse.copy();obj.matrix_basis=margin.matrix_basis.copy()
 mesh.materials.append(bpy.data.materials['V367_LASH_LINE'])
 for p in mesh.polygons:p.use_smooth=True
 obj.shape_key_add(name='Basis');key=obj.shape_key_add(name='Blink')
 for v,p in zip(key.data,states['Blink']):v.co=p
 d=key.driver_add('value').driver;d.type='SCRIPTED';v=d.variables.new();v.name='blink';v.type='SINGLE_PROP';v.targets[0].id=rig;v.targets[0].data_path=f'pose.bones["Head"]["Blink.{side}"]';d.expression='blink'
 report[side]={'lashes':count,'vertices':len(mesh.vertices)}
rig.update_tag();bpy.context.view_layer.update()
report['rig_drivers']=len(rig.animation_data.drivers)
(OUT/'report.json').write_text(json.dumps(report,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Character_An_eyelashes_v394.blend'),compress=True)
print(json.dumps(report))
