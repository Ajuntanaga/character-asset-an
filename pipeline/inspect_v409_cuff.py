import bpy,json
from mathutils import Vector
s=bpy.context.scene;c=s.camera;dg=bpy.context.evaluated_depsgraph_get();result=[];names=set()
for x,y in [(98,72),(110,45),(135,22),(190,27),(202,58),(80,123),(41,112),(62,91),(25,75)]:
 origin=c.matrix_world@Vector(((x/720-.5)*c.data.ortho_scale,(.5-y/640)*c.data.ortho_scale*640/720,0));direction=c.matrix_world.to_quaternion()@Vector((0,0,-1))
 hit,loc,n,i,o,m=s.ray_cast(dg,origin,direction)
 result.append({'pixel':[x,y],'hit':o.name if hit else None,'face':i,'point':list(loc)})
 if hit:names.add(o.name)
print(json.dumps({'rays':result,'objects':[{'name':o.name,'vertices':len(o.data.vertices) if o.type=='MESH' else 0,'modifiers':[(m.name,m.type) for m in o.modifiers],'materials':[m.name if m else None for m in o.data.materials]} for o in (bpy.data.objects[n] for n in names)]}))
