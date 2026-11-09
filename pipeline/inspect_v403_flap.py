import bpy,json
from mathutils import Vector
s=bpy.context.scene;c=s.camera;dg=bpy.context.evaluated_depsgraph_get();result=[]
for x,y in [(110,140),(130,150),(150,160),(170,170),(190,180)]:
 origin=c.matrix_world@Vector(((x/720-.5)*c.data.ortho_scale,(.5-y/640)*c.data.ortho_scale*640/720,0))
 direction=c.matrix_world.to_quaternion()@Vector((0,0,-1))
 hit,loc,n,i,o,m=s.ray_cast(dg,origin,direction)
 result.append({'pixel':[x,y],'hit':o.name if hit else None,'face':i,'point':list(loc)})
print(json.dumps(result))
