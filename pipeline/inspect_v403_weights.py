import bpy,json
from bpy_extras.object_utils import world_to_camera_view
s=bpy.context.scene;o=bpy.data.objects['V357_ANATOMICAL_HAND.R'];m=o.modifiers['Multires'];old=m.levels
try:
 m.levels=0;bpy.context.view_layer.update();e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=e.to_mesh();out=[]
 for v in mesh.vertices:
  c=world_to_camera_view(s,s.camera,e.matrix_world@v.co);x,y=c.x*720,(1-c.y)*640
  if 70<x<210 and 115<y<190:
   base=o.data.vertices[v.index];out.append({'i':v.index,'pixel':[x,y],'co':list(base.co),'weights':[(o.vertex_groups[w.group].name,w.weight) for w in base.groups]})
 e.to_mesh_clear()
finally:m.levels=old;bpy.context.view_layer.update()
print(json.dumps(out))
